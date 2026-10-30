"""Build the Mongia Media site into _site/.

You never need to edit this file. It:
  - reads the text in site.json
  - finds every folder inside photos/ (each folder = one gallery, sorted by folder name)
  - makes web-sized copies of every photo (a large one for the viewer, a small one for grids)
  - writes _site/content.json, which index.html reads

Run locally with:  python scripts/build.py
"""
import json, os, re, shutil, sys
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


def slug(folder):
    return re.sub(r'^\d+[-_ ]*', '', folder).strip().lower().replace(' ', '-').replace('_', '-')


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


def web_name(name):
    return os.path.splitext(name)[0] + '.jpg'


def main():
    site = json.load(open(os.path.join(ROOT, 'site.json'), encoding='utf-8'))
    os.makedirs(OUT, exist_ok=True)
    for f in ['index.html', 'CNAME']:
        if os.path.exists(os.path.join(ROOT, f)):
            shutil.copy(os.path.join(ROOT, f), os.path.join(OUT, f))
    shutil.copytree(os.path.join(ROOT, 'assets'), os.path.join(OUT, 'assets'), dirs_exist_ok=True)
    open(os.path.join(OUT, '.nojekyll'), 'w').close()

    galleries = []
    for folder in sorted(d for d in os.listdir(PHOTOS) if os.path.isdir(os.path.join(PHOTOS, d)) and not d.startswith('.')):
        files = sorted(f for f in os.listdir(os.path.join(PHOTOS, folder)) if f.lower().endswith(EXT) and not f.startswith('.'))
        if not files:
            continue
        meta = site.get('galleries', {}).get(folder, {})
        photos = []
        for f in files:
            src = os.path.join(PHOTOS, folder, f)
            w, h = resize(src, os.path.join(OUT, 'img', 'full', folder, web_name(f)), FULL, 82)
            resize(src, os.path.join(OUT, 'img', 'thumb', folder, web_name(f)), THUMB, 76)
            photos.append({'full': f'img/full/{folder}/{web_name(f)}', 'thumb': f'img/thumb/{folder}/{web_name(f)}', 'w': w, 'h': h})
        cover = meta.get('cover') if meta.get('cover') in files else files[0]
        galleries.append({
            'id': slug(folder),
            'title': meta.get('title') or nice_title(folder),
            'cover': f'img/full/{folder}/{web_name(cover)}',
            'coverPosition': meta.get('coverPosition', '50% 50%'),
            'photos': photos,
        })

    strip = []
    for p in site.get('hero', {}).get('strip', []):
        folder, f = p.split('/', 1)
        if os.path.exists(os.path.join(PHOTOS, folder, f)):
            strip.append(f'img/thumb/{folder}/{web_name(f)}')
    if not strip:  # fall back to the first photos of each gallery
        strip = [ph['thumb'] for g in galleries for ph in g['photos'][:3]]

    json.dump({'site': site, 'galleries': galleries, 'strip': strip}, open(os.path.join(OUT, 'content.json'), 'w', encoding='utf-8'))
    print(f'Built {len(galleries)} galleries, {sum(len(g["photos"]) for g in galleries)} photos into {OUT}')


if __name__ == '__main__':
    main()
