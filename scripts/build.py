"""Build the Mongia Media site into _site/.

You never need to edit this file. It:
  - reads the text in site.json
  - finds every folder inside photos/ (each folder = one gallery, sorted by folder name)
  - makes web-sized copies of every photo (a large one for the viewer, a small one for grids)
  - writes a fully rendered HTML page for the home page and for every gallery,
    plus sitemap.xml, robots.txt, a 404 page and share images, so search engines can read everything

Run locally with:  python scripts/build.py
"""
import datetime, html, json, os, re, shutil, sys
from PIL import Image, ImageOps
try:  # lets you drop iPhone .HEIC photos straight in
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, sys.argv[1] if len(sys.argv) > 1 else '_site')
PHOTOS = os.path.join(ROOT, 'photos')
EXT = ('.jpg', '.jpeg', '.png', '.webp', '.heic')
FULL, THUMB = 1800, 760
NEWTAB = ' target="_blank" rel="noopener"'
e = lambda s: html.escape(str(s), quote=True)


def slug(text):
    text = re.sub(r'^\d+[-_ ]*', '', text).strip().lower()
    return re.sub(r'[^a-z0-9]+', '-', text).strip('-')


def nice_title(folder):
    return re.sub(r'^\d+[-_ ]*', '', folder).replace('-', ' ').replace('_', ' ').strip().title()


def resize(src, dst, edge, quality):
    """Write a resized JPEG; skip if it is already up to date."""
    if os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(src):
        with Image.open(dst) as im:
            return im.size
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with Image.open(src) as im:
        im = ImageOps.exif_transpose(im).convert('RGB')
        im.thumbnail((edge, edge), Image.LANCZOS)
        im.save(dst, 'JPEG', quality=quality, optimize=True, progressive=True)
        return im.size


def share_image(src, dst, pos='50% 50%'):
    """1200x630 crop used when the page is shared on iMessage, Instagram, LinkedIn, etc."""
    if os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(src):
        return
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    try:
        y = float(pos.split()[1].rstrip('%')) / 100
    except Exception:
        y = .5
    with Image.open(src) as im:
        im = ImageOps.exif_transpose(im).convert('RGB')
        ImageOps.fit(im, (1200, 630), Image.LANCZOS, centering=(.5, y)).save(dst, 'JPEG', quality=84, optimize=True)


# ---------- shared page pieces ----------

ICONS = {
    'Instagram': '<rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><path d="M17.5 6.5h.01"/>',
    'WhatsApp': '<path d="M3.5 20.5l1.3-4.3A8.5 8.5 0 1 1 8 19.3z"/><path d="M9.2 8.6c-.3.9 0 2.3 1.4 3.9 1.5 1.6 3 2.2 4 1.9l.6-1.2-1.6-.9-.8.7c-.8-.3-1.6-1.1-2-2l.7-.8-.8-1.6z"/>',
    'LinkedIn': '<rect x="3" y="3" width="18" height="18" rx="3"/><path d="M8 10.5V16M8 7.6v.01M11.5 16v-5.5M11.5 13c0-1.6 1-2.6 2.3-2.6s2.2.9 2.2 2.5V16"/>',
    'Facebook': '<path d="M14.5 21v-7.5h2.6l.4-3h-3V8.6c0-.9.3-1.5 1.5-1.5h1.6V4.4c-.3 0-1.2-.1-2.3-.1-2.3 0-3.8 1.4-3.8 3.9v2.3H9v3h2.5V21"/>',
}


def social_links(c):
    return [('Instagram', 'https://www.instagram.com/' + c['instagram']), ('WhatsApp', c.get('whatsappLink')),
            ('LinkedIn', 'https://www.linkedin.com/in/' + c['linkedin']), ('Facebook', c.get('facebook'))]


def social_html(c):
    out = ''.join(f'<a href="{e(h)}" target="_blank" rel="noopener me" aria-label="Mongia Media on {n}" title="{n}">'
                  f'<svg viewBox="0 0 24 24" aria-hidden="true">{ICONS[n]}</svg></a>' for n, h in social_links(c) if h)
    return f'<span class="social">{out}</span>'


def head(site, title, desc, path, image, extra_ld):
    url = site['url'].rstrip('/') + path
    img = site['url'].rstrip('/') + '/' + image
    ld = ''.join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in extra_ld)
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{e(url)}">
<meta name="robots" content="index,follow,max-image-preview:large">
<meta name="author" content="Rick Mongia">
<meta name="theme-color" content="#000000">
<meta name="geo.region" content="US-NJ">
<meta name="geo.placename" content="New Brunswick">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Mongia Media">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{e(url)}">
<meta property="og:image" content="{e(img)}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:locale" content="en_US">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{e(title)}">
<meta name="twitter:description" content="{e(desc)}">
<meta name="twitter:image" content="{e(img)}">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/assets/favicon-32.png" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600&display=swap">
<link rel="stylesheet" href="/assets/site.css?v={VERSION}">
{ld}
</head>
<body>
'''


def topbar(site, home):
    p = '' if home else '/'
    return f'''<header class="top"><div class="wrap">
  <a class="logo" href="/" aria-label="Mongia Media home"><img src="/assets/logo-white.svg" alt="Mongia Media" width="88" height="35"></a>
  <nav aria-label="Main">
    <a class="hide-sm" href="{p}#work">Work</a>
    <a class="hide-sm" href="{p}#services">Services</a>
    <a class="hide-sm" href="{p}#about">About</a>
    {social_html(site['contact'])}
    <a class="btn light" href="{p}#book">Book a call</a>
  </nav>
</div></header>
'''


def footer(site, home):
    p = '' if home else '/'
    return f'''<footer><div class="wrap">
  <img src="/assets/logo-white.svg" alt="Mongia Media" width="70" height="28" loading="lazy">
  <nav aria-label="Footer"><a href="{p}#work">Work</a><a href="{p}#services">Services</a><a href="{p}#about">About</a><a href="{p}#book">Book</a></nav>
  {social_html(site['contact'])}
  <span>{e(site['footer'])}</span>
</div></footer>
<script src="/assets/site.js?v={VERSION}" defer></script>
</body>
</html>
'''


def business_ld(site, galleries):
    c, url, seo = site['contact'], site['url'].rstrip('/'), site['seo']
    return {
        '@context': 'https://schema.org',
        '@type': ['LocalBusiness', 'ProfessionalService'],
        '@id': url + '/#business',
        'name': 'Mongia Media',
        'alternateName': 'Rixx Flixx',
        'description': seo['description'],
        'url': url + '/',
        'logo': url + '/assets/apple-touch-icon.png',
        'image': url + '/assets/og-home.jpg',
        'email': c['email'],
        'telephone': re.sub(r'[^\d+]', '', c['whatsapp']),
        'priceRange': '$$',
        'address': {'@type': 'PostalAddress', 'addressLocality': seo['city'], 'addressRegion': seo['region'], 'addressCountry': seo['country']},
        'areaServed': [{'@type': 'State', 'name': 'New Jersey'}, {'@type': 'City', 'name': 'New York City'},
                       {'@type': 'City', 'name': 'New Brunswick'}, {'@type': 'City', 'name': 'Seattle'},
                       {'@type': 'State', 'name': 'Washington'}],
        'founder': {'@type': 'Person', '@id': url + '/#rick', 'name': 'Rick Mongia', 'jobTitle': 'Photographer and Videographer',
                    'alumniOf': {'@type': 'CollegeOrUniversity', 'name': 'Rutgers University'},
                    'sameAs': ['https://www.linkedin.com/in/' + c['linkedin']]},
        'sameAs': [h for n, h in social_links(c) if h and n != 'WhatsApp'],
        'knowsAbout': ['Photography', 'Videography'] + [s['title'] for s in site['services']],
        'hasOfferCatalog': {'@type': 'OfferCatalog', 'name': 'Photography and videography services',
                            'itemListElement': [{'@type': 'Offer', 'itemOffered': {'@type': 'Service', 'name': s['title'], 'description': s['text']}} for s in site['services']]},
        'potentialAction': {'@type': 'ReserveAction', 'target': c['booking'], 'name': 'Book a free planning call'},
    }


# ---------- pages ----------

def home_page(site, galleries, strip):
    s, c, seo = site, site['contact'], site['seo']
    url = s['url'].rstrip('/')
    total = sum(len(g['photos']) for g in galleries)
    cards = ''.join(f'<div class="card"><img src="/{e(p["thumb"])}" alt="{e(p["alt"])}" width="{p["tw"]}" height="{p["th"]}" loading="{"eager" if i < 6 else "lazy"}" decoding="async"></div>' for i, p in enumerate(strip))
    tiles = ''.join(
        f'<a class="tile" href="/{g["id"]}/" data-gallery="{g["id"]}" aria-label="{e(g["title"])}, {len(g["photos"])} photos">'
        f'<img src="/{e(g["cover"])}" alt="{e(g["coverAlt"])}" style="object-position:{e(g["coverPosition"])}" loading="{"eager" if i < 3 else "lazy"}" decoding="async">'
        f'<div class="lbl"><h3>{e(g["title"])}</h3><span class="count">{len(g["photos"])} photos</span></div></a>'
        for i, g in enumerate(galleries))
    svc = ''.join(f'<div class="sv"><h3>{e(v["title"])}</h3><p>{e(v["text"])}</p></div>' for v in s['services'])
    about = ''.join(f'<p>{e(p)}</p>' for p in s['about']['paragraphs'])
    rows = [('Email', c['email'], 'mailto:' + c['email'], c['email']), ('WhatsApp', c['whatsapp'], c['whatsappLink'], c['whatsapp']),
            ('Instagram', '@' + c['instagram'], 'https://www.instagram.com/' + c['instagram'], None),
            ('LinkedIn', 'in/' + c['linkedin'], 'https://www.linkedin.com/in/' + c['linkedin'], None), ('Facebook', 'Mongia Media', c['facebook'], None)]
    clist = ''.join(
        f'<div class="crow"><span class="k">{k}</span><span class="v"><a href="{e(h)}"{"" if h.startswith("mailto") else NEWTAB}>{e(v)}</a></span>'
        + (f'<button class="copy-btn" data-copy="{e(cp)}">Copy</button>' if cp else '<span></span>') + '</div>'
        for k, v, h, cp in rows)
    faq = s.get('faq', [])
    faq_html = ''.join(f'<details><summary>{e(f["q"])}</summary><p>{e(f["a"])}</p></details>' for f in faq)
    ld = [business_ld(s, galleries),
          {'@context': 'https://schema.org', '@type': 'WebSite', '@id': url + '/#website', 'url': url + '/', 'name': 'Mongia Media',
           'publisher': {'@id': url + '/#business'}}]
    if faq:
        ld.append({'@context': 'https://schema.org', '@type': 'FAQPage',
                   'mainEntity': [{'@type': 'Question', 'name': f['q'], 'acceptedAnswer': {'@type': 'Answer', 'text': f['a']}} for f in faq]})
    return head(s, seo['title'], seo['description'], '/', 'assets/og-home.jpg', ld) + topbar(s, True) + f'''
<main id="home">
  <section class="hero" id="top">
    <div class="wrap">
      <h1><span class="eyebrow">{e(seo['eyebrow'])}</span>{e(s['hero']['headline'])}</h1>
      <div class="row">
        <div><p class="intro">{e(s['hero']['intro'])}</p><p class="note">{e(s['hero']['note'])}</p></div>
        <div class="acts"><a class="btn light" href="#book">Book a free planning call</a><a class="btn line" href="#work">See the work</a></div>
      </div>
    </div>
    <div class="strip" id="strip" aria-label="Recent photos"><div class="track" id="track">{cards}</div></div>
  </section>

  <section class="block" id="work">
    <div class="wrap">
      <div class="sh"><h2>Work</h2><p>{len(galleries)} galleries, {total} photos. Open one to see the full set.</p></div>
      <div class="bento">{tiles}</div>
    </div>
  </section>

  <section class="block" id="services" style="padding-top:0">
    <div class="wrap">
      <div class="sh"><h2>Services</h2><p>Photo and video for people, events and businesses. Every project starts with a free 30-minute planning call.</p></div>
      <div class="sheet">{svc}</div>
    </div>
  </section>

  <section class="block" id="about" style="padding-top:0">
    <div class="wrap about">
      <figure><img src="/assets/about.jpg" alt="Rick Mongia, photographer and videographer behind Mongia Media, in a black suit and tie" loading="lazy"></figure>
      <div><h2>{e(s['about']['heading'])}</h2><div class="copy">{about}</div><p class="areas">{e(s['about']['areas'])}</p></div>
    </div>
  </section>

  {f"""<section class="block" id="faq" style="padding-top:0">
    <div class="wrap">
      <div class="sh"><h2>Questions</h2><p>Quick answers before we talk.</p></div>
      <div class="faq">{faq_html}</div>
    </div>
  </section>""" if faq else ''}

  <section id="book">
    <div class="wrap book">
      <div>
        <h2>Let's plan your shoot.</h2>
        <p class="sub">Pick a time for a free 30-minute call. We'll go over the vision, locations and timing, and I'll send a quote after.</p>
        <div class="acts"><a class="btn light" href="{e(c['booking'])}" target="_blank" rel="noopener">Choose a time</a><a class="btn line" href="https://www.instagram.com/{e(c['instagram'])}" target="_blank" rel="noopener">Message on Instagram</a></div>
      </div>
      <div class="clist" aria-label="Contact details">{clist}</div>
    </div>
  </section>
</main>
''' + footer(s, True)


def gallery_page(site, galleries, k):
    s, g = site, galleries[k]
    url = s['url'].rstrip('/')
    n = len(galleries)
    prev, nxt = galleries[(k - 1) % n], galleries[(k + 1) % n]
    items = ''.join(
        f'<a href="/{e(p["full"])}" data-full="/{e(p["full"])}" aria-label="Open photo {i + 1} of {len(g["photos"])}">'
        f'<img src="/{e(p["thumb"])}" alt="{e(p["alt"])}" width="{p["tw"]}" height="{p["th"]}" loading="{"eager" if i < 6 else "lazy"}" decoding="async"></a>'
        for i, p in enumerate(g['photos']))
    title = f'{g["seoTitle"]} in NJ, NYC and Seattle | Mongia Media' if g['seoTitle'] not in ('More Work', 'Shot on iPhone') else f'{g["seoTitle"]} | Mongia Media'
    desc = g['intro'] or f'{g["title"]} by Mongia Media.'
    ld = [{'@context': 'https://schema.org', '@type': 'ImageGallery', 'name': f'{g["seoTitle"]} by Mongia Media', 'description': desc,
           'url': f'{url}/{g["id"]}/', 'author': {'@id': url + '/#business'},
           'image': [{'@type': 'ImageObject', 'contentUrl': f'{url}/{p["full"]}', 'thumbnailUrl': f'{url}/{p["thumb"]}', 'caption': p['alt'],
                      'width': p['w'], 'height': p['h'], 'creditText': 'Mongia Media', 'creator': {'@type': 'Person', 'name': 'Rick Mongia'},
                      'copyrightNotice': '© Mongia Media'} for p in g['photos']]},
          {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
              {'@type': 'ListItem', 'position': 1, 'name': 'Home', 'item': url + '/'},
              {'@type': 'ListItem', 'position': 2, 'name': 'Work', 'item': url + '/#work'},
              {'@type': 'ListItem', 'position': 3, 'name': g['title'], 'item': f'{url}/{g["id"]}/'}]}]
    return head(s, title, desc, f'/{g["id"]}/', f'assets/og/{g["id"]}.jpg', ld) + topbar(s, False) + f'''
<main id="gallery">
  <div class="wrap">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a><span aria-hidden="true">/</span><a href="/#work">Work</a><span aria-hidden="true">/</span><span aria-current="page">{e(g['title'])}</span></nav>
    <div class="g-top"><h1>{e(g['seoTitle'])}</h1><span class="meta">{len(g['photos'])} photos</span></div>
    <p class="g-intro">{e(g['intro'])}</p>
    <div class="masonry" id="gGrid" data-title="{e(g['title'])}">{items}</div>
    <div class="g-next"><a href="/{prev['id']}/"><span>Previous gallery</span><b>{e(prev['title'])}</b></a><a href="/{nxt['id']}/"><span>Next gallery</span><b>{e(nxt['title'])}</b></a></div>
  </div>
</main>

<div class="viewer" id="viewer" hidden role="dialog" aria-modal="true" aria-label="Photo viewer">
  <div class="bar"><span id="vCount"></span><button class="vbtn" id="vClose">Close</button></div>
  <div class="stage" id="vStage"><img id="vImg" alt=""></div>
  <button class="vbtn nv prev" id="vPrev" aria-label="Previous photo">&lsaquo;</button>
  <button class="vbtn nv next" id="vNext" aria-label="Next photo">&rsaquo;</button>
  <div class="foot">Swipe or use the arrow keys to move between photos. Press Esc to close.</div>
</div>
''' + footer(s, False)


def not_found(site):
    return head(site, 'Page not found | Mongia Media', 'This page does not exist. Head back to Mongia Media.', '/404.html', 'assets/og-home.jpg', []).replace(
        '<meta name="robots" content="index,follow,max-image-preview:large">', '<meta name="robots" content="noindex">') + topbar(site, False) + '''
<main><div class="wrap nf"><h1>Page not found.</h1><p style="color:var(--fg-2)">That page moved or never existed.</p><div><a class="btn light" href="/">Back to the home page</a></div></div></main>
''' + footer(site, False)


# ---------- build ----------

def main():
    global VERSION
    site = json.load(open(os.path.join(ROOT, 'site.json'), encoding='utf-8'))
    url = site['url'].rstrip('/')
    VERSION = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d%H%M')
    os.makedirs(OUT, exist_ok=True)
    if os.path.exists(os.path.join(ROOT, 'CNAME')):
        shutil.copy(os.path.join(ROOT, 'CNAME'), os.path.join(OUT, 'CNAME'))
    shutil.copytree(os.path.join(ROOT, 'assets'), os.path.join(OUT, 'assets'), dirs_exist_ok=True)
    open(os.path.join(OUT, '.nojekyll'), 'w').close()

    galleries, by_src = [], {}
    for folder in sorted(d for d in os.listdir(PHOTOS) if os.path.isdir(os.path.join(PHOTOS, d)) and not d.startswith('.')):
        files = sorted(f for f in os.listdir(os.path.join(PHOTOS, folder)) if f.lower().endswith(EXT) and not f.startswith('.'))
        if not files:
            continue
        meta = site.get('galleries', {}).get(folder, {})
        gid = slug(folder)
        title = meta.get('title') or nice_title(folder)
        seo_title = meta.get('seoTitle') or title
        photos = []
        for i, f in enumerate(files):
            src = os.path.join(PHOTOS, folder, f)
            name = f'mongia-media-{gid}-{re.sub(r'[^a-z0-9]+', '-', os.path.splitext(f)[0].lower()).strip('-') or i + 1}.jpg'
            w, h = resize(src, os.path.join(OUT, 'img', gid, name), FULL, 82)
            tw, th = resize(src, os.path.join(OUT, 'img', gid, 'sm', name), THUMB, 76)
            alt = (meta.get('alts') or {}).get(f) or f'{seo_title} by Mongia Media, photo {i + 1} of {len(files)}'
            p = {'full': f'img/{gid}/{name}', 'thumb': f'img/{gid}/sm/{name}', 'w': w, 'h': h, 'tw': tw, 'th': th, 'alt': alt, 'src': src}
            photos.append(p)
            by_src[f'{folder}/{f}'] = p
        cover = meta.get('cover') if meta.get('cover') in files else files[0]
        cp = photos[files.index(cover)]
        pos = meta.get('coverPosition', '50% 50%')
        share_image(cp['src'], os.path.join(OUT, 'assets', 'og', f'{gid}.jpg'), pos)
        galleries.append({'id': gid, 'title': title, 'seoTitle': seo_title, 'intro': meta.get('intro', ''),
                          'cover': cp['full'], 'coverAlt': f'{seo_title} by Mongia Media', 'coverPosition': pos, 'photos': photos})

    strip = [by_src[p] for p in site.get('hero', {}).get('strip', []) if p in by_src] or [p for g in galleries for p in g['photos'][:3]]
    first = galleries[0]
    share_image(by_src.get(site['hero'].get('ogImage', ''), first['photos'][0])['src'] if site['hero'].get('ogImage') else
                next(p for p in first['photos'] if p['full'] == first['cover'])['src'],
                os.path.join(OUT, 'assets', 'og-home.jpg'), first['coverPosition'])

    open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8').write(home_page(site, galleries, strip))
    for k, g in enumerate(galleries):
        os.makedirs(os.path.join(OUT, g['id']), exist_ok=True)
        open(os.path.join(OUT, g['id'], 'index.html'), 'w', encoding='utf-8').write(gallery_page(site, galleries, k))
    open(os.path.join(OUT, '404.html'), 'w', encoding='utf-8').write(not_found(site))

    today = datetime.date.today().isoformat()
    def entry(loc, imgs, pri):
        im = ''.join(f'<image:image><image:loc>{e(url + "/" + p["full"])}</image:loc></image:image>' for p in imgs)
        return f'<url><loc>{e(loc)}</loc><lastmod>{today}</lastmod><priority>{pri}</priority>{im}</url>'
    urls = [entry(url + '/', [{'full': g['cover']} for g in galleries], '1.0')] + [entry(f'{url}/{g["id"]}/', g['photos'], '0.8') for g in galleries]
    open(os.path.join(OUT, 'sitemap.xml'), 'w', encoding='utf-8').write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
        'xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n' + '\n'.join(urls) + '\n</urlset>\n')
    open(os.path.join(OUT, 'robots.txt'), 'w').write(f'User-agent: *\nAllow: /\n\nSitemap: {url}/sitemap.xml\n')
    json.dump({'name': 'Mongia Media', 'short_name': 'Mongia Media', 'start_url': '/', 'display': 'browser', 'background_color': '#000000',
               'theme_color': '#000000', 'icons': [{'src': '/assets/apple-touch-icon.png', 'sizes': '180x180', 'type': 'image/png'},
                                                   {'src': '/assets/icon-512.png', 'sizes': '512x512', 'type': 'image/png'}]},
              open(os.path.join(OUT, 'site.webmanifest'), 'w'))
    print(f'Built {len(galleries)} galleries, {sum(len(g["photos"]) for g in galleries)} photos into {OUT}')


VERSION = ''
if __name__ == '__main__':
    main()
