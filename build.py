import os
import glob
import json
from bs4 import BeautifulSoup
import re

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_PATH = os.path.join(BASE_DIR, 'index.html')
BLOG_DIR = os.path.join(BASE_DIR, 'blog')

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
        
        # Try to find description
        desc = ""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            desc = meta_desc['content']
            
        # Try to find date (schema or time tag)
        date = "2024-01-01"
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

def process_blog_files(nav_template, footer_template, favicons, all_posts):
    blog_files = glob.glob(os.path.join(BLOG_DIR, '*.html'))
    
    for file_path in blog_files:
        print(f"Processing {file_path}...")
        soup = BeautifulSoup(read_file(file_path), 'html.parser')
        filename = os.path.basename(file_path)
        is_blog_index = (filename == 'index.html')
        
        # --- Phase 2: Head Reconstruction ---
        head = soup.head
        if not head:
            head = soup.new_tag('head')
            soup.insert(0, head)
            
        # Extract existing metadata to preserve
        title_tag = head.find('title')
        title_text = title_tag.text if title_tag else "Join Ouyi"
        
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
        filename = os.path.basename(file_path)
        slug = filename.replace('.html', '')
        canonical_url = f"https://join-ouyi.top/blog/{slug}"
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
            
        # 3. Smart Recommendations
        if not is_blog_index:
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
                    if post['url'] == f"/blog/{slug}": continue
                    if post['url'].endswith('/index'): continue # Skip blog index
                    if count >= 2: break
                    
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
        
        # Update Blog Index Grid
        if is_blog_index:
            update_blog_index_grid(soup, all_posts)

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
                
        write_file(file_path, str(soup))

def main():
    print("Starting build process...")
    
    # 1. Parse Index
    index_soup, nav, footer, favicons = process_index()
    
    # 2. Get Blog Metadata
    posts = extract_blog_metadata()
    
    # 3. Process Blog Files
    process_blog_files(nav, footer, favicons, posts)
    
    # 4. Update Index Blog Section
    update_index_blog_section(index_soup, posts)
    write_file(INDEX_PATH, str(index_soup))
    
    print("Build complete.")

if __name__ == "__main__":
    main()
