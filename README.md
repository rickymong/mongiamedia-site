# Mongia Media website

The site rebuilds itself every time you change something in this repo. You never have to touch the code.

## Add photos

1. On GitHub, open the `photos` folder, then the gallery you want (for example `05-street`).
2. Click **Add file > Upload files**, drag your photos in, and click **Commit changes**.
3. Wait about 2 minutes. The site updates on its own.

Notes:
- Upload full-size JPGs straight from Lightroom or your phone (iPhone .HEIC works too). The site makes web-sized copies automatically.
- Photos show in filename order. Name them `01.jpg`, `02.jpg`, and so on to control the order.
- To delete a photo, open it on GitHub, click the **...** menu, then **Delete file**.

## Add a new gallery

Create a new folder inside `photos`, for example `08-real-estate`, and upload photos into it.
- The number at the front sets where it appears on the page. The rest becomes the title ("Real Estate").
- To pick a different title or cover photo, add a line under `"galleries"` in `site.json`:
  `"08-real-estate": { "title": "Real Estate", "cover": "04.jpg" },`

## Change text

All the wording (headline, intro, services, about, contact links, footer) is in `site.json`.
Open it on GitHub, click the pencil icon, edit the text between the quotes, and click **Commit changes**.
Keep the quotes and commas where they are.

## Change the cover photo of a gallery

In `site.json`, change `"cover"` for that gallery to the photo's filename.
If the important part gets cropped, add `"coverPosition": "50% 100%"` (keeps the bottom) or `"50% 0%"` (keeps the top).

## Hosting and your domain

The site is hosted for free on GitHub Pages. `CNAME` holds the domain, `mongiamedia.com`.

DNS records to add at your domain registrar (GoDaddy):

| Type  | Name | Value                 |
|-------|------|-----------------------|
| A     | @    | 185.199.108.153       |
| A     | @    | 185.199.109.153       |
| A     | @    | 185.199.110.153       |
| A     | @    | 185.199.111.153       |
| CNAME | www  | rickymong.github.io   |

Remove any other A records on `@` and any old `www` record that points to Adobe Portfolio.
Keep the MX records, because those run your rick@mongiamedia.com email.
Then on GitHub go to **Settings > Pages**, confirm the custom domain, and tick **Enforce HTTPS** once it's available.

## Preview on your computer (optional)

```
pip install pillow pillow-heif
python scripts/build.py
python -m http.server --directory _site 8000
```
Then open http://localhost:8000.
