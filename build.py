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

# Icons & Categories
CATEGORY_ICONS = {
    'Security': '<svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"></path></svg>',
    'Guide': '<svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path></svg>',
    'Trading': '<svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path></svg>',
    'Tools': '<svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>',
    'Review': '<svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3"></path></svg>',
    'Web3': '<svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.384-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"></path></svg>'
}

def clean_link(href):
    if not href: return href
    if href.startswith('http'): return href
    if href.startswith('#'): return href
    if href.endswith('.html'): return href[:-5]
    return href

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

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
            
        # Determine Category
        category = "Web3"
        cat_keywords = {
            'Security': ['安全', '风险', '冻结', '验证', '骗局', 'Safety'],
            'Guide': ['注册', '开户', '入金', '下载', '教程', '指南', 'Guide'],
            'Trading': ['手续费', '费率', '合约', '杠杆', '交易', 'Fee', 'Trading'],
            'Tools': ['查询', '浏览器', '追踪', '工具', 'Query'],
            'Review': ['对比', '评测', '评价', 'VS', '哪个好', 'Review']
        }
        
        for cat, keywords in cat_keywords.items():
            if any(k.lower() in title.lower() for k in keywords):
                category = cat
                break

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
            'category': category,
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
        
        # Overlay
        overlay = soup.new_tag('div', **{'class': 'absolute inset-0 bg-black/20 group-hover:bg-transparent transition-colors'})
        img_div.append(overlay)

        # Determine Category for Icon
        cat = post.get('category', 'Web3')
        
        # Badge with Icon (Same style as blog index)
        badge = soup.new_tag('div', **{'class': 'absolute top-4 left-4 px-3 py-1.5 bg-white/10 backdrop-blur-md border border-white/10 rounded-full text-[10px] font-bold text-white uppercase tracking-wider flex items-center gap-1.5 z-10'})
        
        # Icon
        icon_svg = CATEGORY_ICONS.get(cat, CATEGORY_ICONS['Web3'])
        # Parse SVG string to tag
        icon_soup = BeautifulSoup(icon_svg, 'html.parser')
        icon_tag = icon_soup.svg
        # Fix viewBox casing for HTML parser
        if icon_tag.has_attr('viewbox'):
            icon_tag['viewBox'] = icon_tag['viewbox']
            del icon_tag['viewbox']
        badge.append(icon_tag)
        
        span_cat = soup.new_tag('span')
        span_cat.string = cat.upper()
        badge.append(span_cat)
        
        img_div.append(badge)

        # Centered Big Icon (Watermark)
        center_icon_div = soup.new_tag('div', **{'class': 'absolute inset-0 flex items-center justify-center opacity-20 group-hover:opacity-30 group-hover:scale-110 transition-all duration-500'})
        big_icon_soup = BeautifulSoup(icon_svg, 'html.parser')
        big_icon_tag = big_icon_soup.svg
        if big_icon_tag.has_attr('viewbox'):
            big_icon_tag['viewBox'] = big_icon_tag['viewbox']
            del big_icon_tag['viewbox']
        # Change class to be larger
        big_icon_tag['class'] = 'w-24 h-24 text-white'
        center_icon_div.append(big_icon_tag)
        img_div.append(center_icon_div)

        article.append(img_div)
        
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
    """Regenerate the article grid in blog/index.html with categories and pagination."""
    main_tag = soup.find('main')
    if not main_tag: return
    
    # 1. Insert Category Filter (Tabs)
    # Check if exists, else insert before grid
    filter_div = main_tag.find('div', id='category-filter')
    if not filter_div:
        filter_div = soup.new_tag('div', id='category-filter', **{'class': 'flex flex-wrap gap-3 mb-12 justify-center'})
        
        categories = ['All', 'Guide', 'Trading', 'Security', 'Tools', 'Review']
        cat_labels = {'All': '全部', 'Guide': '新手教程', 'Trading': '交易费率', 'Security': '安全风控', 'Tools': '实用工具', 'Review': '深度评测'}
        
        for cat in categories:
            btn = soup.new_tag('button', **{
                'class': f'px-4 py-2 rounded-full text-sm font-medium transition-all duration-300 {"bg-white text-black font-bold" if cat == "All" else "bg-white/5 text-txt-muted hover:bg-white/10 hover:text-white"}',
                'data-filter': cat,
                'onclick': "filterPosts(this)"
            })
            btn.string = cat_labels.get(cat, cat)
            filter_div.append(btn)
            
        # Insert after header (which is usually h1/p)
        header = main_tag.find('header')
        if header:
            header.insert_after(filter_div)
        else:
            main_tag.insert(0, filter_div)

    # Find or create the grid container
    grid_ul = main_tag.find('ul', class_='grid')
    if not grid_ul:
        grid_ul = soup.new_tag('ul', **{'class': 'grid md:grid-cols-2 lg:grid-cols-3 gap-8', 'id': 'posts-grid'})
        main_tag.append(grid_ul)
    else:
        grid_ul['id'] = 'posts-grid'
    
    grid_ul.clear()
    
    # Filter out index.html itself
    valid_posts = [p for p in posts if not p['url'].endswith('/index')]
    
    for post in valid_posts:
        cat = post.get('category', 'Web3')
        li = soup.new_tag('li', **{'class': 'h-full fade-up', 'data-category': cat})
        
        # Article Card
        article = soup.new_tag('article', **{'class': 'flex flex-col h-full bg-[#121212] border border-white/10 rounded-3xl overflow-hidden hover:border-primary/50 hover:shadow-2xl hover:shadow-primary/10 transition-all duration-300 group relative'})
        
        # Image Area
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
        
        # Badge with Icon
        badge = soup.new_tag('div', **{'class': 'absolute top-4 left-4 px-3 py-1.5 bg-white/10 backdrop-blur-md border border-white/10 rounded-full text-[10px] font-bold text-white uppercase tracking-wider flex items-center gap-1.5 z-10'})
        
        # Icon
        icon_svg = CATEGORY_ICONS.get(cat, CATEGORY_ICONS['Web3'])
        # Parse SVG string to tag
        icon_soup = BeautifulSoup(icon_svg, 'html.parser')
        icon_tag = icon_soup.svg
        # Fix viewBox casing for HTML parser
        if icon_tag.has_attr('viewbox'):
            icon_tag['viewBox'] = icon_tag['viewbox']
            del icon_tag['viewbox']
        badge.append(icon_tag)
        
        span_cat = soup.new_tag('span')
        span_cat.string = cat.upper()
        badge.append(span_cat)
        
        img_div.append(badge)

        # Centered Big Icon (Watermark)
        center_icon_div = soup.new_tag('div', **{'class': 'absolute inset-0 flex items-center justify-center opacity-20 group-hover:opacity-30 group-hover:scale-110 transition-all duration-500'})
        big_icon_soup = BeautifulSoup(icon_svg, 'html.parser')
        big_icon_tag = big_icon_soup.svg
        if big_icon_tag.has_attr('viewbox'):
            big_icon_tag['viewBox'] = big_icon_tag['viewbox']
            del big_icon_tag['viewbox']
        # Change class to be larger
        big_icon_tag['class'] = 'w-24 h-24 text-white'
        # Remove stroke if it's stroke-based, or keep it. Let's keep as is but large.
        center_icon_div.append(big_icon_tag)
        img_div.append(center_icon_div)
        
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

    # Pagination Controls
    pagination_div = main_tag.find('div', id='pagination-controls')
    if not pagination_div:
        pagination_div = soup.new_tag('div', id='pagination-controls', **{'class': 'mt-16 flex justify-center gap-2'})
        # We will populate this via JS, but add a placeholder or structure
        main_tag.append(pagination_div)
    
    # Inject JS for Interactivity
    script_id = "blog-interactive-js"
    existing_script = soup.find('script', id=script_id)
    if existing_script:
        existing_script.decompose()
        
    js_code = """
    document.addEventListener('DOMContentLoaded', function() {
        const posts = Array.from(document.querySelectorAll('#posts-grid > li'));
        const buttons = document.querySelectorAll('#category-filter button');
        const paginationContainer = document.getElementById('pagination-controls');
        const ITEMS_PER_PAGE = 9;
        let currentPage = 1;
        let currentFilter = 'All';
        let visiblePosts = [];

        function filterPosts(category) {
            currentFilter = category;
            currentPage = 1;
            
            // Update buttons
            buttons.forEach(btn => {
                if(btn.dataset.filter === category) {
                    btn.classList.remove('bg-white/5', 'text-txt-muted');
                    btn.classList.add('bg-white', 'text-black', 'font-bold');
                } else {
                    btn.classList.add('bg-white/5', 'text-txt-muted');
                    btn.classList.remove('bg-white', 'text-black', 'font-bold');
                }
            });

            // Filter logic
            if (category === 'All') {
                visiblePosts = posts;
            } else {
                visiblePosts = posts.filter(post => post.dataset.category === category);
            }
            
            renderPosts();
        }

        function renderPosts() {
            // Hide all first
            posts.forEach(p => p.classList.add('hidden'));
            
            // Calculate slice
            const start = (currentPage - 1) * ITEMS_PER_PAGE;
            const end = start + ITEMS_PER_PAGE;
            const pagePosts = visiblePosts.slice(start, end);
            
            // Show current page posts
            pagePosts.forEach(p => {
                p.classList.remove('hidden');
                // Trigger animation reset if needed
                p.style.animation = 'none';
                p.offsetHeight; /* trigger reflow */
                p.style.animation = null;
            });
            
            renderPagination();
        }

        function renderPagination() {
            paginationContainer.innerHTML = '';
            const totalPages = Math.ceil(visiblePosts.length / ITEMS_PER_PAGE);
            
            if (totalPages <= 1) return;
            
            // Prev
            const prevBtn = document.createElement('button');
            prevBtn.innerHTML = '←';
            prevBtn.className = `w-10 h-10 rounded-full border border-white/10 flex items-center justify-center transition-colors ${currentPage === 1 ? 'text-txt-muted cursor-not-allowed' : 'text-white hover:bg-white/10'}`;
            prevBtn.onclick = () => { if(currentPage > 1) { currentPage--; renderPosts(); window.scrollTo({top: 0, behavior: 'smooth'}); }};
            paginationContainer.appendChild(prevBtn);
            
            // Pages
            for (let i = 1; i <= totalPages; i++) {
                const btn = document.createElement('button');
                btn.innerText = i;
                btn.className = `w-10 h-10 rounded-full border border-white/10 flex items-center justify-center transition-colors ${currentPage === i ? 'bg-primary text-white border-primary' : 'text-txt-muted hover:bg-white/10 hover:text-white'}`;
                btn.onclick = () => { currentPage = i; renderPosts(); window.scrollTo({top: 0, behavior: 'smooth'}); };
                paginationContainer.appendChild(btn);
            }
            
            // Next
            const nextBtn = document.createElement('button');
            nextBtn.innerHTML = '→';
            nextBtn.className = `w-10 h-10 rounded-full border border-white/10 flex items-center justify-center transition-colors ${currentPage === totalPages ? 'text-txt-muted cursor-not-allowed' : 'text-white hover:bg-white/10'}`;
            nextBtn.onclick = () => { if(currentPage < totalPages) { currentPage++; renderPosts(); window.scrollTo({top: 0, behavior: 'smooth'}); }};
            paginationContainer.appendChild(nextBtn);
        }

        // Expose to global for HTML onclick
        window.filterPosts = function(btn) {
            filterPosts(btn.dataset.filter);
        };

        // Init
        visiblePosts = posts;
        renderPosts();
    });
    """
    
    script_tag = soup.new_tag('script', id=script_id)
    script_tag.string = js_code
    soup.body.append(script_tag)

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
        head.append(soup.new_tag('meta', attrs={"name": "distribution", "content": "global"}))
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
            script_tag.string = json.dumps(schema_data, ensure_ascii=False, indent=2)
            schemas.append(script_tag)

        # Ensure BreadcrumbList for Blog Posts
        if is_blog and not is_index:
            has_breadcrumb = False
            for schema in schemas:
                if not schema.string: continue
                try:
                    data = json.loads(schema.string)
                    if data.get('@type') == 'BreadcrumbList':
                        has_breadcrumb = True
                    if '@graph' in data:
                        for item in data['@graph']:
                            if item.get('@type') == 'BreadcrumbList':
                                has_breadcrumb = True
                except:
                    pass
            
            if not has_breadcrumb:
                breadcrumb_data = {
                    "@context": "https://schema.org",
                    "@type": "BreadcrumbList",
                    "itemListElement": [
                        {
                            "@type": "ListItem",
                            "position": 1,
                            "name": "首页",
                            "item": "https://join-ouyi.top/"
                        },
                        {
                            "@type": "ListItem",
                            "position": 2,
                            "name": "Web3 知识库",
                            "item": "https://join-ouyi.top/blog/"
                        },
                        {
                            "@type": "ListItem",
                            "position": 3,
                            "name": title_text,
                            "item": canonical_url
                        }
                    ]
                }
                bc_script = soup.new_tag('script', type='application/ld+json')
                bc_script.string = json.dumps(breadcrumb_data, ensure_ascii=False, indent=2)
                schemas.append(bc_script)

        # Re-format all schemas to ensure indentation
        for schema in schemas:
            if schema.string:
                try:
                    data = json.loads(schema.string)
                    schema.string = json.dumps(data, ensure_ascii=False, indent=2)
                except:
                    pass
            head.append(schema)
            head.append('\n')

        # --- Phase 3: Content Injection ---
        
        # 1. Layout Sync (Nav & Footer)
        if nav_template:
            old_nav = soup.find('nav')
            new_nav = nav_template.__copy__()
            
            # Convert anchor links in nav to root-relative for ALL sub-pages
            for a in new_nav.find_all('a'):
                href = a.get('href')
                if href and href.startswith('#'):
                    a['href'] = '/' + href
            
            if old_nav:
                old_nav.replace_with(new_nav)
            else:
                if soup.body: soup.body.insert(0, new_nav)
            
        if footer_template:
            old_footer = soup.find('footer')
            new_footer = footer_template.__copy__()
            
            # Convert anchor links in footer to root-relative for ALL sub-pages
            for a in new_footer.find_all('a'):
                href = a.get('href')
                if href and href.startswith('#'):
                    a['href'] = '/' + href
                        
            if old_footer:
                old_footer.replace_with(new_footer)
            else:
                if soup.body: soup.body.append(new_footer)
            
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
