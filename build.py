import os
import glob
import json
from bs4 import BeautifulSoup
import re

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_PATH = os.path.join(BASE_DIR, 'index.html')
BLOG_DIR = os.path.join(BASE_DIR, 'blog')
LEGAL_DIR = os.path.join(BASE_DIR, 'legal')
HELP_DIR = os.path.join(BASE_DIR, 'help')
SITEMAP_PATH = os.path.join(BASE_DIR, 'sitemap.xml')

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def clean_link(href):
    if not href: return href
    if href.startswith('http'): return href
    if href.startswith('#'): return href
    if href.endswith('.html'): return href[:-5]
    return href

def get_favicons(soup):
    icons = []
    # Extract all icon related tags
    for rel in ['icon', 'shortcut icon', 'apple-touch-icon']:
        for link in soup.find_all('link', rel=rel):
            href = link.get('href')
            if href:
                # Ensure root relative path
                if not href.startswith('/') and not href.startswith('http'):
                    href = '/' + href
                link['href'] = href
                icons.append(link)
    return icons

def extract_blog_metadata():
    """Extract metadata from all blog posts for the home page."""
    blog_files = glob.glob(os.path.join(BLOG_DIR, '*.html'))
    posts = []
    
    for file_path in blog_files:
        soup = BeautifulSoup(read_file(file_path), 'html.parser')
        filename = os.path.basename(file_path)
        slug = filename.replace('.html', '')
        
        title = soup.title.string if soup.title else slug
        if title:
            # Clean title by removing suffix after |
            if '|' in title:
                title = title.split('|')[0]
            # Remove years like 2024, 2025, 2026
            title = re.sub(r'\s*202[0-9]\s*', ' ', title)
            title = title.strip()
        
        # Try to find description
        desc = ""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            desc = meta_desc['content']
            
        # Try to find date (schema or time tag)
        date = "2024-01-01"
        
        # Priority 1: Schema datePublished
        schema_tag = soup.find('script', type='application/ld+json')
        if schema_tag:
            try:
                data = json.loads(schema_tag.string)
                if 'datePublished' in data:
                    date = data['datePublished']
            except:
                pass
                
        # Priority 2: time tag
        if date == "2024-01-01":
            time_tag = soup.find('time')
            if time_tag and time_tag.get('datetime'):
                date = time_tag['datetime']
            
        posts.append({
            'title': title,
            'desc': desc,
            'url': f"/blog/{slug}",
            'date': date,
            'file_path': file_path
        })
        
    # Sort by date (if possible) or just reverse
    posts.sort(key=lambda x: x['date'], reverse=True)
    return posts

def update_sitemap(posts):
    """Update sitemap.xml with all blog posts, updating timestamps if changed."""
    if not os.path.exists(SITEMAP_PATH):
        return

    try:
        # Read existing sitemap
        with open(SITEMAP_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'xml')
        urlset = soup.find('urlset')
        
        # Map existing URLs to their <url> tags
        existing_entries = {}
        for url_tag in urlset.find_all('url'):
            loc = url_tag.find('loc')
            if loc:
                existing_entries[loc.text.strip()] = url_tag
        
        base_url = "https://join-ouyi.top"
        updated_count = 0
        added_count = 0
        
        for post in posts:
            full_url = f"{base_url}{post['url']}"
            new_date = post['date']
            
            if full_url in existing_entries:
                # Check if date needs update
                url_tag = existing_entries[full_url]
                lastmod = url_tag.find('lastmod')
                if lastmod and lastmod.text != new_date:
                    lastmod.string = new_date
                    updated_count += 1
            else:
                # Add new entry
                new_url_tag = soup.new_tag('url')
                
                loc = soup.new_tag('loc')
                loc.string = full_url
                new_url_tag.append(loc)
                
                lastmod = soup.new_tag('lastmod')
                lastmod.string = new_date
                new_url_tag.append(lastmod)
                
                priority = soup.new_tag('priority')
                priority.string = "0.80"
                new_url_tag.append(priority)
                
                urlset.append(new_url_tag)
                added_count += 1
        
        # Write back (using prettify might change format, so let's try to keep it simple or accept standard XML format)
        # Using standard string conversion for BS4 XML
        write_file(SITEMAP_PATH, str(soup))
        
        if added_count > 0 or updated_count > 0:
            print(f"Sitemap updated: {added_count} added, {updated_count} timestamps updated.")
        else:
            print("Sitemap is up to date.")
            
    except Exception as e:
        print(f"Error updating sitemap: {e}")

def update_index_blog_section(soup, posts):
    """Update the blog section in index.html with latest posts."""
    blog_section = soup.find('section', id='blog')
    if not blog_section:
        return
        
    grid_container = blog_section.find('div', class_='grid')
    if not grid_container:
        return
        
    # Clear existing posts
    grid_container.clear()
    
    # Add posts (limit to 3 for home page)
    # Filter out index.html from homepage blog section if present
    display_posts = [p for p in posts if not p['url'].endswith('/index')][:3]
    
    for post in display_posts:
        article = soup.new_tag('article', **{'class': 'relative group bg-card border border-border rounded-3xl overflow-hidden hover:border-blue-500/30 transition-all duration-300 flex flex-col h-full'})
        
        # Image div (placeholder gradient)
        # Using a deterministic gradient based on title length to give variety
        gradients = [
            'from-purple-900/20 to-black',
            'from-blue-900/20 to-black',
            'from-indigo-900/20 to-black',
            'from-emerald-900/20 to-black'
        ]
        grad_cls = gradients[len(post['title']) % len(gradients)]
        
        img_div = soup.new_tag('div', **{'class': f'h-48 bg-gradient-to-br {grad_cls} relative overflow-hidden'})
        article.append(img_div)
        
        # Overlay
        overlay = soup.new_tag('div', **{'class': 'absolute inset-0 bg-black/20 group-hover:bg-transparent transition-colors'})
        img_div.append(overlay)
        
        content_div = soup.new_tag('div', **{'class': 'p-8 flex flex-col flex-grow'})
        
        # Meta info
        meta_div = soup.new_tag('div', **{'class': 'text-xs text-txt-muted mb-3 flex items-center gap-2'})
        time_tag = soup.new_tag('time')
        time_tag.string = post['date']
        meta_div.append(time_tag)
        content_div.append(meta_div)
        
        # Title
        h3 = soup.new_tag('h3', **{'class': 'text-xl font-bold text-white mb-3 group-hover:text-blue-400 transition-colors'})
        a = soup.new_tag('a', href=post['url'], **{'class': 'focus:outline-none'})
        span_inset = soup.new_tag('span', **{'class': 'absolute inset-0 z-10'})
        a.append(span_inset)
        a.append(post['title'])
        h3.append(a)
        content_div.append(h3)
        
        # Description
        p = soup.new_tag('p', **{'class': 'text-sm text-txt-muted leading-relaxed mb-6 flex-grow line-clamp-3'})
        p.string = post['desc']
        content_div.append(p)
        
        # Read more
        read_more = soup.new_tag('div', **{'class': 'flex items-center text-sm font-medium text-white group-hover:translate-x-2 transition-transform'})
        read_more.string = "阅读全文"
        # Arrow icon
        svg = soup.new_tag('svg', **{'class': 'w-4 h-4 ml-2', 'fill': 'none', 'stroke': 'currentColor', 'viewBox': '0 0 24 24'})
        path = soup.new_tag('path', **{'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', 'd': 'M17 8l4 4m0 0l-4 4m4-4H3'})
        svg.append(path)
        read_more.append(svg)
        
        content_div.append(read_more)
        
        article.append(content_div)
        grid_container.append(article)

def process_index():
    soup = BeautifulSoup(read_file(INDEX_PATH), 'html.parser')
    
    # 1. Extract Nav & Footer
    nav = soup.find('nav')
    footer = soup.find('footer')
    
    # Clean links in nav/footer
    if nav:
        for a in nav.find_all('a'):
            if a.get('href'): a['href'] = clean_link(a['href'])
    if footer:
        for a in footer.find_all('a'):
            if a.get('href'): a['href'] = clean_link(a['href'])
        
    # 2. Extract Brand Assets (Favicons)
    favicons = get_favicons(soup)
    
    return soup, nav, footer, favicons

def update_blog_index_grid(soup, posts):
    """Regenerate the article grid in blog/index.html."""
    main_tag = soup.find('main')
    if not main_tag: return
    
    # Find or create the grid container
    grid_ul = main_tag.find('ul', class_='grid')
    if not grid_ul:
        # Try to find where to insert if missing, or just append to main
        grid_ul = soup.new_tag('ul', **{'class': 'grid md:grid-cols-2 lg:grid-cols-3 gap-8'})
        main_tag.append(grid_ul)
    
    grid_ul.clear()
    
    # Filter out index.html itself
    valid_posts = [p for p in posts if not p['url'].endswith('/index')]
    
    for post in valid_posts:
        li = soup.new_tag('li', **{'class': 'h-full fade-up'})
        
        # Article Card
        article = soup.new_tag('article', **{'class': 'flex flex-col h-full bg-[#121212] border border-white/10 rounded-3xl overflow-hidden hover:border-primary/50 hover:shadow-2xl hover:shadow-primary/10 transition-all duration-300 group relative'})
        
        # Image Area (Gradient Placeholder)
        # Using a deterministic gradient based on title length to give variety
        gradients = [
            'from-purple-900/20 to-black',
            'from-blue-900/20 to-black',
            'from-indigo-900/20 to-black',
            'from-emerald-900/20 to-black'
        ]
        grad_cls = gradients[len(post['title']) % len(gradients)]
        
        img_div = soup.new_tag('div', **{'class': f'h-48 bg-gradient-to-br {grad_cls} relative overflow-hidden'})
        
        # Decorate
        overlay = soup.new_tag('div', **{'class': 'absolute inset-0 bg-black/20 group-hover:bg-transparent transition-colors'})
        img_div.append(overlay)
        
        # Badge
        badge = soup.new_tag('div', **{'class': 'absolute top-4 left-4 px-3 py-1 bg-white/10 backdrop-blur-md border border-white/10 rounded-full text-[10px] font-bold text-white uppercase tracking-wider'})
        badge.string = "Article"
        img_div.append(badge)
        
        article.append(img_div)
        
        # Content Area
        content = soup.new_tag('div', **{'class': 'p-6 flex flex-col flex-grow'})
        
        # Date
        meta = soup.new_tag('div', **{'class': 'flex items-center gap-2 text-xs text-txt-muted mb-3'})
        time_tag = soup.new_tag('time')
        time_tag.string = post['date']
        meta.append(time_tag)
        content.append(meta)
        
        # Title
        h2 = soup.new_tag('h2', **{'class': 'text-xl font-bold text-white mb-3 leading-tight group-hover:text-primary transition-colors'})
        a_link = soup.new_tag('a', href=post['url'], **{'class': 'focus:outline-none'})
        span_inset = soup.new_tag('span', **{'class': 'absolute inset-0 z-10'}) # Full card clickable
        a_link.append(span_inset)
        a_link.string = post['title']
        h2.append(a_link)
        content.append(h2)
        
        # Desc
        p = soup.new_tag('p', **{'class': 'text-sm text-txt-muted line-clamp-3 mb-6 flex-grow'})
        p.string = post['desc']
        content.append(p)
        
        # Footer / Read More
        footer_div = soup.new_tag('div', **{'class': 'flex items-center justify-between pt-4 border-t border-white/5'})
        
        read_more = soup.new_tag('span', **{'class': 'text-sm font-medium text-white group-hover:translate-x-1 transition-transform inline-flex items-center gap-1'})
        read_more.string = "阅读全文"
        # Arrow icon
        svg = soup.new_tag('svg', **{'class': 'w-4 h-4', 'fill': 'none', 'stroke': 'currentColor', 'viewBox': '0 0 24 24'})
        path = soup.new_tag('path', **{'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', 'd': 'M17 8l4 4m0 0l-4 4m4-4H3'})
        svg.append(path)
        read_more.append(svg)
        
        footer_div.append(read_more)
        
        content.append(footer_div)
        article.append(content)
        li.append(article)
        grid_ul.append(li)

def update_blog_index_schema(soup, posts):
    """Update the JSON-LD schema in blog/index.html to include all articles."""
    schema_tag = soup.find('script', type='application/ld+json')
    if not schema_tag:
        return

    try:
        data = json.loads(schema_tag.string)
        
        target_list = None
        
        # We prefer updating CollectionPage > mainEntity > ItemList
        # Also we want to remove any standalone ItemList to avoid duplicates
        
        if '@graph' in data:
            collection_page = None
            standalone_item_list_indices = []
            
            for i, item in enumerate(data['@graph']):
                if item.get('@type') == 'CollectionPage':
                    collection_page = item
                elif item.get('@type') == 'ItemList':
                    standalone_item_list_indices.append(i)
            
            # If we have a CollectionPage, use its mainEntity
            if collection_page:
                if 'mainEntity' not in collection_page:
                    collection_page['mainEntity'] = {"@type": "ItemList", "itemListElement": []}
                elif collection_page['mainEntity'].get('@type') != 'ItemList':
                     # If mainEntity exists but isn't ItemList, maybe wrap it or ignore? 
                     # For this specific project, we overwrite/ensure it is ItemList
                     collection_page['mainEntity'] = {"@type": "ItemList", "itemListElement": []}
                
                target_list = collection_page['mainEntity']
                
                # Remove standalone ItemLists as they are redundant
                for i in sorted(standalone_item_list_indices, reverse=True):
                    del data['@graph'][i]
            
            # Fallback: If no CollectionPage, use or create standalone ItemList
            elif standalone_item_list_indices:
                target_list = data['@graph'][standalone_item_list_indices[0]]
            else:
                 target_list = {
                    "@type": "ItemList",
                    "itemListElement": []
                 }
                 data['@graph'].append(target_list)
                 
        else:
            # Not a graph, just a single object
            if data.get('@type') == 'CollectionPage':
                 if 'mainEntity' not in data:
                    data['mainEntity'] = {"@type": "ItemList", "itemListElement": []}
                 target_list = data['mainEntity']
            elif data.get('@type') == 'ItemList':
                target_list = data
            
        if target_list:
            # Rebuild itemListElement
            elements = []
            valid_posts = [p for p in posts if not p['url'].endswith('/index')]
            
            for i, post in enumerate(valid_posts):
                elements.append({
                    "@type": "ListItem",
                    "position": i + 1,
                    "url": f"https://join-ouyi.top{post['url']}",
                    "name": post['title']
                })
            
            target_list['itemListElement'] = elements
            target_list['numberOfItems'] = len(elements)
            
            # Update the tag
            schema_tag.string = json.dumps(data, ensure_ascii=False, indent=2)
            
    except Exception as e:
        print(f"Error updating schema: {e}")

def create_sidebar(soup, all_posts, current_url):
    """Generate a high-end sidebar with CTA and latest articles."""
    aside = soup.new_tag('aside', **{'class': 'lg:col-span-4 space-y-8'})
    sticky_div = soup.new_tag('div', **{'class': 'sticky top-24 space-y-6'})
    aside.append(sticky_div)

    # 1. High-End CTA Card
    cta_card = soup.new_tag('div', **{'class': 'relative overflow-hidden rounded-3xl bg-gradient-to-br from-[#1a1a1a] to-black border border-white/10 group hover:border-primary/50 transition-all duration-500 shadow-2xl'})
    
    # Glow effect
    glow = soup.new_tag('div', **{'class': 'absolute -top-10 -right-10 w-32 h-32 bg-primary/20 rounded-full blur-[50px] group-hover:bg-primary/30 transition-all duration-500'})
    cta_card.append(glow)
    
    cta_content = soup.new_tag('div', **{'class': 'p-6 relative z-10 text-center'})
    
    # Icon or Badge
    badge = soup.new_tag('div', **{'class': 'inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-xs font-bold text-primary mb-4'})
    badge.string = "限时福利"
    cta_content.append(badge)
    
    h3 = soup.new_tag('h3', **{'class': 'text-2xl font-black text-white mb-2'})
    h3.string = "注册 OKX"
    cta_content.append(h3)
    
    p = soup.new_tag('p', **{'class': 'text-sm text-txt-muted mb-6'})
    p.string = "领取最高 100 USDT 数字货币盲盒"
    cta_content.append(p)
    
    btn = soup.new_tag('a', href="/#hero", **{'class': 'block w-full py-3.5 bg-gradient-to-r from-primary to-blue-600 hover:from-blue-600 hover:to-primary text-white rounded-xl font-bold text-sm tracking-wide shadow-lg shadow-primary/25 hover:shadow-primary/40 hover:-translate-y-0.5 transition-all duration-300'})
    btn.string = "立即领取"
    cta_content.append(btn)
    
    cta_card.append(cta_content)
    sticky_div.append(cta_card)

    # 2. Latest/Relevant Articles List
    list_card = soup.new_tag('div', **{'class': 'bg-card/50 backdrop-blur-sm border border-white/5 rounded-3xl p-6'})
    list_title = soup.new_tag('h4', **{'class': 'text-sm font-bold text-white uppercase tracking-wider mb-4 opacity-80'})
    list_title.string = "最新文章 (Latest)"
    list_card.append(list_title)
    
    ul = soup.new_tag('ul', **{'class': 'space-y-4'})
    
    count = 0
    for post in all_posts:
        if post['url'] == current_url: continue
        if post['url'].endswith('/index'): continue
        if count >= 5: break
        
        li = soup.new_tag('li')
        a = soup.new_tag('a', href=post['url'], **{'class': 'group flex gap-3 items-start'})
        
        # Number or Dot
        dot = soup.new_tag('span', **{'class': 'mt-1.5 w-1.5 h-1.5 rounded-full bg-white/20 group-hover:bg-primary transition-colors flex-shrink-0'})
        a.append(dot)
        
        div_text = soup.new_tag('div')
        h5 = soup.new_tag('h5', **{'class': 'text-sm text-txt-muted group-hover:text-white transition-colors line-clamp-2 leading-relaxed'})
        h5.string = post['title']
        div_text.append(h5)
        
        a.append(div_text)
        li.append(a)
        ul.append(li)
        count += 1
        
    list_card.append(ul)
    sticky_div.append(list_card)
    
    return aside

def process_pages(files, nav_template, footer_template, favicons, all_posts, is_blog=False):
    for file_path in files:
        print(f"Processing {file_path}...")
        soup = BeautifulSoup(read_file(file_path), 'html.parser')
        filename = os.path.basename(file_path)
        is_index = (filename == 'index.html')
        
        # --- Phase 2: Head Reconstruction ---
        head = soup.head
        if not head:
            head = soup.new_tag('head')
            soup.insert(0, head)
            
        # Extract existing metadata to preserve
        title_tag = head.find('title')
        title_text = title_tag.text if title_tag else "Join Ouyi"
        
        # Clean title text
        if '|' in title_text:
            title_text = title_text.split('|')[0]
        title_text = re.sub(r'\s*202[0-9]\s*', ' ', title_text).strip()
        
        meta_desc = head.find('meta', attrs={'name': 'description'})
        desc_content = meta_desc['content'] if meta_desc else ""
        
        meta_kw = head.find('meta', attrs={'name': 'keywords'})
        kw_content = meta_kw['content'] if meta_kw else ""
        
        # Preserve specific scripts/styles (Tailwind, etc.)
        existing_assets = []
        for tag in head.find_all(['script', 'style', 'link']):
            # Skip favicons as we inject new ones
            if tag.name == 'link' and any(x in tag.get('rel', []) for x in ['icon', 'shortcut', 'apple-touch-icon']):
                continue
            # Skip canonical/robots as we reconstruct them
            if tag.name == 'link' and tag.get('rel') == ['canonical']:
                continue
            # Skip hreflang as we reconstruct them
            if tag.name == 'link' and 'alternate' in tag.get('rel', []):
                continue
            if tag.name == 'meta': continue
            if tag.name == 'title': continue
            existing_assets.append(tag)
            
        # Preserve Schema
        schemas = head.find_all('script', type='application/ld+json')
        
        # Clear Head
        head.clear()
        
        # Group A: Basic Meta
        head.append(soup.new_tag('meta', charset="utf-8"))
        head.append('\n')
        head.append(soup.new_tag('meta', attrs={"name": "viewport", "content": "width=device-width, initial-scale=1.0"}))
        head.append('\n')
        new_title = soup.new_tag('title')
        new_title.string = title_text
        head.append(new_title)
        head.append('\n')
        
        # Group B: SEO Core
        if desc_content:
            head.append(soup.new_tag('meta', attrs={"name": "description", "content": desc_content}))
            head.append('\n')
        if kw_content:
            head.append(soup.new_tag('meta', attrs={"name": "keywords", "content": kw_content}))
            head.append('\n')
            
        # Canonical
        rel_path = os.path.relpath(file_path, BASE_DIR)
        url_part = rel_path.replace(os.sep, '/').replace('.html', '')
        if url_part.endswith('/index'):
            url_part = url_part[:-6]
        canonical_url = f"https://join-ouyi.top/{url_part}"

        head.append(soup.new_tag('link', rel="canonical", href=canonical_url))
        head.append('\n')
        
        # Group C: Indexing & Geo
        head.append(soup.new_tag('meta', attrs={"name": "robots", "content": "index, follow"}))
        head.append('\n')
        head.append(soup.new_tag('meta', attrs={"http-equiv": "content-language", "content": "zh-CN"}))
        head.append('\n')
        
        # Hreflang
        for lang in ['zh-CN', 'zh', 'x-default']:
            head.append(soup.new_tag('link', rel="alternate", hreflang=lang, href=canonical_url))
            head.append('\n')
            
        # Group D: Brand & Resources
        # Inject Favicons
        for icon in favicons:
            head.append(icon.__copy__())
            head.append('\n')
            
        # Inject preserved assets (CSS/JS)
        for asset in existing_assets:
            head.append(asset)
            head.append('\n')
            
        # Group E: Schema
        if not schemas:
            schema_data = {
                "@context": "https://schema.org",
                "@type": "WebPage",
                "name": title_text,
                "description": desc_content,
                "url": canonical_url
            }
            script_tag = soup.new_tag('script', type='application/ld+json')
            script_tag.string = json.dumps(schema_data, ensure_ascii=False)
            schemas.append(script_tag)

        for schema in schemas:
            head.append(schema)
            head.append('\n')

        # --- Phase 3: Content Injection ---
        
        # 1. Layout Sync (Nav & Footer)
        if nav_template:
            old_nav = soup.find('nav')
            if old_nav:
                old_nav.replace_with(nav_template.__copy__())
            else:
                if soup.body: soup.body.insert(0, nav_template.__copy__())
            
        if footer_template:
            old_footer = soup.find('footer')
            if old_footer:
                old_footer.replace_with(footer_template.__copy__())
            else:
                if soup.body: soup.body.append(footer_template.__copy__())
            
        # 2. Sidebar Injection (Blog Only)
        if is_blog and not is_index:
            # Try to find aside to replace, or append to main if main is grid
            main_tag = soup.find('main')
            if main_tag:
                # Assuming main has grid layout: grid-cols-1 lg:grid-cols-12
                # We want to replace existing aside or insert new one
                old_aside = main_tag.find('aside')
                
                # Generate new sidebar
                current_url = f"/{url_part}"
                new_aside = create_sidebar(soup, all_posts, current_url)
                
                if old_aside:
                    old_aside.replace_with(new_aside)
                else:
                    # If no aside but main exists, check if we should add it
                    # Only add if it looks like a blog post (has article)
                    if main_tag.find('article'):
                        main_tag.append(new_aside)

        # 3. Smart Recommendations (Blog Only)
        if is_blog and not is_index:
            article = soup.find('article')
            if article:
                # Check if we already have recommendations to avoid duplicate
                existing_rec = article.find('div', class_='recommendations-injected')
                if existing_rec:
                    existing_rec.decompose()
                    
                rec_section = soup.new_tag('div', **{'class': 'recommendations-injected mt-12 pt-8 border-t border-white/10'})
                h3 = soup.new_tag('h3', **{'class': 'text-xl font-bold text-white mb-6'})
                h3.string = "推荐阅读"
                rec_section.append(h3)
                
                rec_grid = soup.new_tag('div', **{'class': 'grid md:grid-cols-2 gap-4'})
                
                # Add other posts as recommendations (exclude current and index)
                count = 0
                for post in all_posts:
                    if post['url'] == f"/{url_part}": continue
                    if post['url'].endswith('/index'): continue # Skip blog index
                    if count >= 4: break
                    
                    a_link = soup.new_tag('a', href=post['url'], **{'class': 'block p-4 rounded-xl bg-white/5 hover:bg-white/10 transition-colors'})
                    h4 = soup.new_tag('h4', **{'class': 'text-white font-bold mb-2'})
                    h4.string = post['title']
                    a_link.append(h4)
                    
                    p_desc = soup.new_tag('p', **{'class': 'text-xs text-txt-muted line-clamp-2'})
                    p_desc.string = post['desc']
                    a_link.append(p_desc)
                    
                    rec_grid.append(a_link)
                    count += 1
                    
                rec_section.append(rec_grid)
                article.append(rec_section)
        
        # Update Blog Index Grid (Blog Only)
        if is_blog and is_index:
            update_blog_index_grid(soup, all_posts)
            update_blog_index_schema(soup, all_posts)

        # Remove hardcoded "Related Reading" section if exists
        for section in soup.find_all('section'):
            h2 = section.find('h2')
            if h2 and "相关阅读" in h2.get_text():
                section.decompose()
            
        # 4. Global Link Cleaning (remove .html) inside body
        if soup.body:
            for a in soup.body.find_all('a'):
                href = a.get('href')
                if href:
                    a['href'] = clean_link(href)
            
            # Fix Breadcrumb Links (Web3 Knowledge Base)
            if is_blog and not is_index:
                nav_crumb = soup.find('nav', attrs={'aria-label': '面包屑导航'})
                if nav_crumb:
                    for a in nav_crumb.find_all('a'):
                        # Check if it points to #blog or old anchor
                        if a.get('href') in ['/#blog', '/blog/guide.html', '/blog/guide']: 
                             # But wait, guide is the article. We want the parent category link.
                             # Usually the breadcrumb is Home > Web3 Knowledge Base > Article
                             # So we look for the one named "Web3 知识库"
                             if "Web3" in a.get_text() or "知识库" in a.get_text():
                                 a['href'] = "/blog/"

        write_file(file_path, str(soup))

def main():
    print("Starting build process...")
    
    # 1. Parse Index
    index_soup, nav, footer, favicons = process_index()
    
    # 2. Get Blog Metadata
    posts = extract_blog_metadata()
    
    # 3. Process Blog Files
    blog_files = glob.glob(os.path.join(BLOG_DIR, '*.html'))
    process_pages(blog_files, nav, footer, favicons, posts, is_blog=True)

    # 4. Process Legal & Help Files
    other_files = glob.glob(os.path.join(LEGAL_DIR, '*.html')) + glob.glob(os.path.join(HELP_DIR, '*.html'))
    process_pages(other_files, nav, footer, favicons, posts, is_blog=False)
    
    # 5. Update Index Blog Section
    update_index_blog_section(index_soup, posts)
    write_file(INDEX_PATH, str(index_soup))
    
    # 6. Update Sitemap
    update_sitemap(posts)
    
    print("Build complete.")

if __name__ == "__main__":
    main()
