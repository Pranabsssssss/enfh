import json, re, os

with open('all_bucket_keys.json', 'r', encoding='utf-8') as f:
    all_keys = json.load(f)

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

def extract_question_number(filename, default_idx):
    m = re.search(r'\^?\((\d+)\)', filename)
    if m:
        return int(m.group(1))
    m2 = re.search(r'Q(\d+)', filename, re.IGNORECASE)
    if m2:
        return int(m2.group(1))
    m3 = re.search(r'(\d+)', filename)
    if m3:
        return int(m3.group(1))
    return default_idx

def map_subject(sub_code):
    sub = sub_code.upper()
    if 'P-NEE' in sub or 'P-JEE' in sub or sub == 'P' or 'PHY' in sub:
        return 'Physics'
    if 'C-NEE' in sub or 'C-JEE' in sub or sub == 'C' or 'CHEM' in sub:
        return 'Chemistry'
    if 'M-JEE' in sub or sub == 'M' or 'MATH' in sub:
        return 'Mathematics'
    if 'B-NEE' in sub or sub == 'B' or 'BIO' in sub:
        return 'Biology'
    return sub_code.capitalize()

def format_exam_title(raw_name):
    name = raw_name
    name = name.replace('XIITH', '12th Class')
    name = name.replace('XITH', '11th Class')
    name = name.replace('-COPY-fa9d', ' (Copy)')
    name = re.sub(r'-COPY-[a-f0-9]+', ' (Copy)', name)
    name = name.replace('-', ' ')
    name = re.sub(r'\s+', ' ', name).strip()
    return name

from collections import defaultdict
folders = defaultdict(list)
for k in all_keys:
    parts = k.split('/')
    folder = '/'.join(parts[:-1])
    fname = parts[-1]
    folders[folder].append(fname)

for f in folders:
    folders[f] = sorted(list(set(folders[f])), key=natural_sort_key)

def categorize_folder(folder_path):
    u = folder_path.upper()
    if 'XITH-NEET' in u or '11-NEET' in u or 'CLASS-11-NEET' in u:
        return '11th NEET Major Tests', 'neet-11', 'badge-neet', 1
    if 'XIITH-NEET' in u and 'MAJOR' in u:
        return '12th NEET Major Tests', 'neet-12', 'badge-neet', 2
    if 'XITH-IIT' in u or 'CLASS-11-JEE' in u:
        return '11th JEE Major Tests', 'jee-11', 'badge-jee', 3
    if 'XIITH-IIT' in u and 'MAJOR' in u:
        return '12th JEE Major Tests', 'jee-12', 'badge-jee', 4
    if 'MINOR' in u:
        return 'NEET & IIT Minor Tests', 'minor', 'badge-minor', 5
    if 'CLASS-9' in u or 'AIET' in u:
        return 'Class 9 Foundation Tests', 'class-9', 'badge-foundation', 6
    if any(k in u for k in ['AI-MOCK', 'DEMO', 'IMPTEST', 'ORIGINAL-TEST', 'NEWFEATURES', 'MOCK', 'EXAM-082026', 'TEST-LOCKING']):
        return 'Mock & Feature Tests', 'mock', 'badge-mock', 7
    if 'MAT' in u:
        return 'Mental Ability (MAT)', 'mat', 'badge-mat', 8
    cnt = len(folders[folder_path])
    if cnt == 25:
        return 'Topic Tests (25Q)', 'topic-25', 'badge-topic', 9
    if cnt == 20:
        return 'Topic Tests (20Q)', 'topic-20', 'badge-topic', 10
    if cnt == 1 or any('SCREENSHOT' in x.upper() for x in folders[folder_path]):
        return 'Single Screenshots', 'screenshot', 'badge-screenshot', 12
    return 'Practice Question Sets', 'practice', 'badge-topic', 11

exam_groups = defaultdict(lambda: {
    'folders': [],
    'category': '',
    'cat_key': '',
    'badge_class': '',
    'priority': 99
})

for f in sorted(folders.keys()):
    cat_name, cat_key, badge_class, prio = categorize_folder(f)
    folder_base = f.split('/')[-1]
    if '__' in folder_base:
        exam_id = folder_base.split('__')[0]
        prefix_part = '/'.join(f.split('/')[:-1])
        full_exam_key = f"{prefix_part}/{exam_id}" if prefix_part else exam_id
    else:
        full_exam_key = f

    exam_groups[full_exam_key]['folders'].append(f)
    exam_groups[full_exam_key]['category'] = cat_name
    exam_groups[full_exam_key]['cat_key'] = cat_key
    exam_groups[full_exam_key]['badge_class'] = badge_class
    exam_groups[full_exam_key]['priority'] = prio

sub_order = {'Physics': 1, 'Chemistry': 2, 'Mathematics': 3, 'Biology': 4, 'Mental Ability': 5}

paper_list = []
for exam_key, group in sorted(exam_groups.items()):
    raw_name = exam_key.split('/')[-1]
    if group['cat_key'] in ['topic-25', 'topic-20', 'practice', 'screenshot']:
        hash_id = raw_name
        title = f"{group['category']} — {hash_id[:8]}"
        is_topic = True
    else:
        title = format_exam_title(raw_name)
        is_topic = False

    subjects_data = []
    total_q = 0

    for f_path in group['folders']:
        if '__' in f_path:
            raw_sub = f_path.split('__')[-1]
            sub_name = map_subject(raw_sub)
        else:
            sub_name = "Practice Set" if is_topic else "General"

        file_list = folders[f_path]
        q_items = []
        for idx, fn in enumerate(file_list, start=1):
            q_num = extract_question_number(fn, idx)
            key_path = f"{f_path}/{fn}"
            local_rel_url = f"./{f_path}/{fn}"
            q_items.append({
                'num': q_num,
                'idx': idx,
                'filename': fn,
                'url': local_rel_url,
                'key': key_path
            })
        
        q_items.sort(key=lambda x: x['num'])
        total_q += len(q_items)
        subjects_data.append({
            'code': sub_name.lower().replace(' ', '-'),
            'name': sub_name,
            'raw_code': f_path,
            'folder': f_path,
            'count': len(q_items),
            'questions': q_items
        })

    subjects_data.sort(key=lambda s: sub_order.get(s['name'], 99))
    clean_id = re.sub(r'[^a-zA-Z0-9_-]', '_', exam_key)
    subtitle = f"{group['category']} • {total_q} Questions • {', '.join([s['name'] for s in subjects_data])}"

    paper_list.append({
        'id': clean_id,
        'title': title,
        'category': group['category'],
        'category_key': group['cat_key'],
        'badge_class': group['badge_class'],
        'priority': group['priority'],
        'total_questions': total_q,
        'subtitle': subtitle,
        'subjects': subjects_data
    })

paper_list.sort(key=lambda p: (p['priority'], p['title']))
data_json = json.dumps(paper_list, ensure_ascii=False)

html_template = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes">
  <meta name="mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <title>Question Papers</title>
  <style>
    :root {{
      --bg-body: #0d1117;
      --bg-surface: #161b22;
      --bg-surface-elevated: #21262d;
      --bg-card: #181d26;
      --bg-card-header: #1f242e;
      --border-color: #30363d;
      --border-focus: #58a6ff;
      --text-main: #f0f6fc;
      --text-muted: #8b949e;
      --text-dim: #6e7681;
      
      --accent-primary: #38bdf8;
      --accent-gradient: linear-gradient(135deg, #38bdf8 0%, #6366f1 100%);
      
      --physics-color: #3b82f6;
      --physics-bg: rgba(59, 130, 246, 0.15);
      --chemistry-color: #a855f7;
      --chemistry-bg: rgba(168, 85, 247, 0.15);
      --math-color: #f97316;
      --math-bg: rgba(249, 115, 22, 0.15);
      --bio-color: #10b981;
      --bio-bg: rgba(16, 185, 129, 0.15);
      --mat-color: #06b6d4;
      --mat-bg: rgba(6, 182, 212, 0.15);

      --radius-sm: 8px;
      --radius-md: 12px;
      --radius-lg: 16px;
      --radius-pill: 9999px;

      --shadow-sm: 0 2px 6px rgba(0, 0, 0, 0.25);
      --shadow-md: 0 8px 24px rgba(0, 0, 0, 0.35);
      --shadow-lg: 0 16px 40px rgba(0, 0, 0, 0.5);
    }}

    [data-theme="light"] {{
      --bg-body: #f8fafc;
      --bg-surface: #ffffff;
      --bg-surface-elevated: #f1f5f9;
      --bg-card: #ffffff;
      --bg-card-header: #f8fafc;
      --border-color: #e2e8f0;
      --border-focus: #0284c7;
      --text-main: #0f172a;
      --text-muted: #64748b;
      --text-dim: #94a3b8;
      --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.05);
      --shadow-md: 0 8px 20px rgba(0, 0, 0, 0.08);
      --shadow-lg: 0 16px 36px rgba(0, 0, 0, 0.12);
    }}

    /* Global Security & Anti-Inspection Protections */
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      -webkit-user-select: none !important;
      -moz-user-select: none !important;
      -ms-user-select: none !important;
      user-select: none !important;
      -webkit-touch-callout: none !important;
      -webkit-user-drag: none !important;
      -webkit-tap-highlight-color: transparent;
    }}

    img {{
      -webkit-user-drag: none !important;
      -khtml-user-drag: none !important;
      -moz-user-drag: none !important;
      -o-user-drag: none !important;
      user-drag: none !important;
      user-select: none !important;
      -webkit-user-select: none !important;
      -webkit-touch-callout: none !important;
      pointer-events: auto;
    }}

    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      background-color: var(--bg-body);
      color: var(--text-main);
      line-height: 1.5;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      transition: background-color 0.25s ease, color 0.25s ease;
      -webkit-user-select: none !important;
      user-select: none !important;
      overflow-x: hidden;
    }}

    /* Header */
    header.portal-header {{
      position: sticky;
      top: 0;
      z-index: 900;
      background: var(--bg-surface);
      border-bottom: 1px solid var(--border-color);
      box-shadow: var(--shadow-sm);
      backdrop-filter: blur(12px);
    }}

    .header-top {{
      max-width: 1560px;
      margin: 0 auto;
      padding: 12px 20px 8px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }}

    .header-title-text {{
      font-size: 20px;
      font-weight: 800;
      letter-spacing: -0.02em;
      color: var(--text-main);
    }}

    .header-actions {{
      display: flex;
      align-items: center;
      gap: 8px;
      flex-shrink: 0;
    }}

    .btn {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      padding: 8px 14px;
      border-radius: var(--radius-sm);
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      border: 1px solid var(--border-color);
      background: var(--bg-surface-elevated);
      color: var(--text-main);
      transition: all 0.18s ease;
      text-decoration: none;
      min-height: 38px;
      touch-action: manipulation;
    }}

    .btn:hover {{
      background: var(--border-color);
      transform: translateY(-1px);
    }}

    .btn-icon {{
      padding: 8px 12px;
      min-width: 38px;
    }}

    /* Control Bar */
    .control-bar {{
      max-width: 1560px;
      margin: 0 auto;
      padding: 6px 20px 14px;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }}

    .paper-picker-row {{
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
    }}

    .select-wrapper {{
      position: relative;
      flex: 1 1 280px;
      min-width: 0;
    }}

    select.paper-select {{
      width: 100%;
      padding: 10px 36px 10px 12px;
      background: var(--bg-surface-elevated);
      border: 1px solid var(--border-color);
      color: var(--text-main);
      border-radius: var(--radius-md);
      font-size: 14px;
      font-weight: 600;
      font-family: inherit;
      outline: none;
      cursor: pointer;
      appearance: none;
      transition: border-color 0.2s, box-shadow 0.2s;
      min-height: 42px;
    }}

    select.paper-select:focus {{
      border-color: var(--border-focus);
      box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.2);
    }}

    .select-chevron {{
      position: absolute;
      right: 14px;
      top: 50%;
      transform: translateY(-50%);
      pointer-events: none;
      color: var(--text-muted);
      font-size: 12px;
    }}

    .search-box {{
      position: relative;
      flex: 0 1 240px;
      min-width: 160px;
    }}

    .search-input {{
      width: 100%;
      padding: 10px 14px 10px 34px;
      background: var(--bg-surface-elevated);
      border: 1px solid var(--border-color);
      color: var(--text-main);
      border-radius: var(--radius-md);
      font-size: 13px;
      font-family: inherit;
      outline: none;
      transition: border-color 0.2s;
      min-height: 42px;
    }}

    .search-input:focus {{
      border-color: var(--border-focus);
    }}

    .search-icon {{
      position: absolute;
      left: 12px;
      top: 50%;
      transform: translateY(-50%);
      color: var(--text-muted);
      pointer-events: none;
    }}

    /* Category Filter Chips */
    .category-chips {{
      display: flex;
      gap: 8px;
      overflow-x: auto;
      padding-bottom: 4px;
      scrollbar-width: thin;
      width: 100%;
      -webkit-overflow-scrolling: touch;
    }}

    .category-chip {{
      padding: 7px 14px;
      border-radius: var(--radius-pill);
      background: var(--bg-surface-elevated);
      color: var(--text-muted);
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      border: 1px solid var(--border-color);
      white-space: nowrap;
      transition: all 0.18s;
      user-select: none;
      min-height: 34px;
      display: inline-flex;
      align-items: center;
    }}

    .category-chip:hover {{
      color: var(--text-main);
      border-color: var(--text-dim);
    }}

    .category-chip.active {{
      background: var(--text-main);
      color: var(--bg-body);
      border-color: var(--text-main);
      font-weight: 700;
    }}

    /* Exam Details Banner */
    .exam-banner {{
      background: var(--bg-surface);
      border-bottom: 1px solid var(--border-color);
      padding: 16px 20px;
    }}

    .banner-inner {{
      max-width: 1560px;
      margin: 0 auto;
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 16px;
      flex-wrap: wrap;
    }}

    .banner-info {{
      flex: 1 1 300px;
      min-width: 0;
    }}

    .banner-info h2 {{
      font-size: 22px;
      font-weight: 800;
      letter-spacing: -0.02em;
      margin-bottom: 6px;
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
      word-break: break-word;
    }}

    .badge {{
      display: inline-block;
      padding: 3px 10px;
      border-radius: var(--radius-pill);
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      flex-shrink: 0;
    }}

    .badge-neet {{ background: var(--bio-bg); color: var(--bio-color); border: 1px solid var(--bio-color); }}
    .badge-jee {{ background: var(--physics-bg); color: var(--physics-color); border: 1px solid var(--physics-color); }}
    .badge-minor {{ background: var(--chemistry-bg); color: var(--chemistry-color); border: 1px solid var(--chemistry-color); }}
    .badge-mock {{ background: var(--math-bg); color: var(--math-color); border: 1px solid var(--math-color); }}
    .badge-foundation {{ background: rgba(236, 72, 153, 0.15); color: #ec4899; border: 1px solid #ec4899; }}
    .badge-mat {{ background: var(--mat-bg); color: var(--mat-color); border: 1px solid var(--mat-color); }}
    .badge-topic {{ background: rgba(148, 163, 184, 0.15); color: #94a3b8; border: 1px solid #64748b; }}
    .badge-screenshot {{ background: rgba(234, 179, 8, 0.15); color: #eab308; border: 1px solid #eab308; }}

    .banner-subtitle {{
      color: var(--text-muted);
      font-size: 13px;
      font-weight: 500;
      word-break: break-word;
    }}

    .banner-stats {{
      display: flex;
      gap: 10px;
      align-items: center;
      flex-shrink: 0;
    }}

    .stat-box {{
      background: var(--bg-surface-elevated);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-md);
      padding: 8px 14px;
      text-align: center;
      min-width: 75px;
    }}

    .stat-value {{
      font-size: 17px;
      font-weight: 800;
      font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
      color: var(--accent-primary);
    }}

    .stat-label {{
      font-size: 10px;
      color: var(--text-muted);
      text-transform: uppercase;
      font-weight: 600;
    }}

    /* Subject Tabs & Jump Bar */
    .nav-bar-sticky {{
      background: var(--bg-surface);
      border-bottom: 1px solid var(--border-color);
      padding: 8px 20px;
    }}

    .nav-bar-inner {{
      max-width: 1560px;
      margin: 0 auto;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      flex-wrap: wrap;
    }}

    .subject-tabs {{
      display: flex;
      gap: 8px;
      overflow-x: auto;
      -webkit-overflow-scrolling: touch;
      padding-bottom: 2px;
      flex: 1 1 auto;
    }}

    .tab-btn {{
      padding: 8px 16px;
      border-radius: var(--radius-sm);
      font-size: 13px;
      font-weight: 700;
      cursor: pointer;
      border: 1px solid var(--border-color);
      background: var(--bg-surface-elevated);
      color: var(--text-muted);
      display: flex;
      align-items: center;
      gap: 7px;
      transition: all 0.2s;
      white-space: nowrap;
      min-height: 38px;
      touch-action: manipulation;
    }}

    .tab-btn:hover {{
      color: var(--text-main);
      transform: translateY(-1px);
    }}

    .tab-btn.active {{
      background: var(--bg-card);
      color: var(--text-main);
      border-color: var(--border-focus);
      box-shadow: 0 0 0 1px var(--border-focus);
    }}

    .tab-btn.active.tab-physics {{ border-color: var(--physics-color); box-shadow: 0 0 0 1px var(--physics-color); color: var(--physics-color); }}
    .tab-btn.active.tab-chemistry {{ border-color: var(--chemistry-color); box-shadow: 0 0 0 1px var(--chemistry-color); color: var(--chemistry-color); }}
    .tab-btn.active.tab-mathematics {{ border-color: var(--math-color); box-shadow: 0 0 0 1px var(--math-color); color: var(--math-color); }}
    .tab-btn.active.tab-biology {{ border-color: var(--bio-color); box-shadow: 0 0 0 1px var(--bio-color); color: var(--bio-color); }}
    .tab-btn.active.tab-mat {{ border-color: var(--mat-color); box-shadow: 0 0 0 1px var(--mat-color); color: var(--mat-color); }}

    .tab-count {{
      font-size: 11px;
      padding: 2px 7px;
      border-radius: var(--radius-pill);
      background: rgba(255, 255, 255, 0.08);
    }}

    .view-mode-toggle {{
      display: flex;
      border: 1px solid var(--border-color);
      border-radius: var(--radius-sm);
      overflow: hidden;
      background: var(--bg-surface-elevated);
      flex-shrink: 0;
    }}

    .view-btn {{
      padding: 8px 12px;
      border: none;
      background: transparent;
      color: var(--text-muted);
      cursor: pointer;
      font-size: 12px;
      font-weight: 600;
      transition: all 0.15s;
      min-height: 38px;
      touch-action: manipulation;
    }}

    .view-btn.active {{
      background: var(--accent-gradient);
      color: white;
    }}

    /* Jump Navigator Palette */
    .jump-palette-container {{
      max-width: 1560px;
      margin: 12px auto 0;
      padding: 0 20px;
    }}

    .jump-palette {{
      background: var(--bg-surface);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-md);
      padding: 10px 14px;
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      max-height: 110px;
      overflow-y: auto;
      scrollbar-width: thin;
      -webkit-overflow-scrolling: touch;
    }}

    .jump-label {{
      width: 100%;
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-muted);
      margin-bottom: 2px;
    }}

    .jump-pill {{
      width: 34px;
      height: 32px;
      border-radius: 6px;
      border: 1px solid var(--border-color);
      background: var(--bg-surface-elevated);
      color: var(--text-muted);
      font-size: 12px;
      font-weight: 700;
      font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      transition: all 0.15s;
      text-decoration: none;
      touch-action: manipulation;
    }}

    .jump-pill:hover, .jump-pill:active {{
      background: var(--text-main);
      color: var(--bg-body);
      border-color: var(--text-main);
      transform: scale(1.06);
    }}

    /* Main Content */
    main.content-area {{
      max-width: 1560px;
      margin: 18px auto 60px;
      padding: 0 20px;
      flex: 1;
      width: 100%;
    }}

    .grid-view {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
      gap: 18px;
    }}

    .focus-view {{
      display: flex;
      flex-direction: column;
      gap: 20px;
      max-width: 900px;
      margin: 0 auto;
    }}

    .card {{
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-md);
      overflow: hidden;
      box-shadow: var(--shadow-sm);
      display: flex;
      flex-direction: column;
      transition: transform 0.2s, box-shadow 0.2s, border-color 0.2s;
    }}

    .card:hover {{
      border-color: var(--text-dim);
      box-shadow: var(--shadow-md);
    }}

    .card.highlighted {{
      border-color: var(--accent-primary);
      box-shadow: 0 0 0 2px var(--accent-primary), var(--shadow-md);
      animation: pulseHighlight 1.5s ease-out;
    }}

    @keyframes pulseHighlight {{
      0% {{ transform: scale(1.02); }}
      50% {{ transform: scale(1); }}
      100% {{ transform: scale(1); }}
    }}

    .card-header {{
      background: var(--bg-card-header);
      border-bottom: 1px solid var(--border-color);
      padding: 10px 14px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
    }}

    .card-header-title {{
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    .q-number {{
      font-size: 13px;
      font-weight: 800;
      color: var(--text-main);
      font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
    }}

    .q-subject-tag {{
      font-size: 11px;
      font-weight: 700;
      padding: 2px 8px;
      border-radius: var(--radius-pill);
      background: var(--bg-surface-elevated);
      color: var(--text-muted);
    }}

    .card-header-actions {{
      display: flex;
      align-items: center;
      gap: 6px;
    }}

    .card-btn {{
      background: var(--bg-surface-elevated);
      border: 1px solid var(--border-color);
      color: var(--text-muted);
      cursor: pointer;
      padding: 6px 10px;
      border-radius: 6px;
      font-size: 12px;
      display: inline-flex;
      align-items: center;
      gap: 4px;
      text-decoration: none;
      transition: all 0.15s;
      min-height: 32px;
      touch-action: manipulation;
    }}

    .card-btn:hover, .card-btn:active {{
      color: var(--text-main);
      border-color: var(--text-dim);
    }}

    .image-box {{
      padding: 14px;
      background: #ffffff;
      min-height: 120px;
      display: flex;
      align-items: center;
      justify-content: center;
      position: relative;
      cursor: zoom-in;
      overflow-x: auto;
    }}

    .question-img {{
      max-width: 100%;
      height: auto;
      display: block;
      transition: opacity 0.2s;
    }}

    .card-footer {{
      padding: 8px 14px;
      background: var(--bg-card);
      border-top: 1px solid var(--border-color);
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 11px;
      color: var(--text-dim);
    }}

    /* Lightbox Modal */
    .lightbox-modal {{
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.92);
      backdrop-filter: blur(8px);
      z-index: 10000;
      display: none;
      flex-direction: column;
      align-items: center;
      justify-content: space-between;
      padding: 14px;
      user-select: none;
      touch-action: none;
    }}

    .lightbox-modal.active {{
      display: flex;
    }}

    .lightbox-header {{
      width: 100%;
      max-width: 1200px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      color: white;
      gap: 8px;
    }}

    .lightbox-title {{
      font-size: 15px;
      font-weight: 700;
      font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}

    .lightbox-controls {{
      display: flex;
      align-items: center;
      gap: 6px;
      flex-shrink: 0;
    }}

    .lightbox-btn {{
      background: rgba(255, 255, 255, 0.15);
      border: 1px solid rgba(255, 255, 255, 0.25);
      color: white;
      padding: 7px 12px;
      border-radius: var(--radius-sm);
      cursor: pointer;
      font-size: 13px;
      font-weight: 600;
      transition: all 0.15s;
      min-height: 36px;
      touch-action: manipulation;
    }}

    .lightbox-btn:hover, .lightbox-btn:active {{
      background: rgba(255, 255, 255, 0.3);
    }}

    .lightbox-body {{
      flex: 1;
      width: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
      position: relative;
      overflow: hidden;
      padding: 8px;
    }}

    .lightbox-img-wrapper {{
      display: inline-block;
      transition: transform 0.12s ease-out;
      background: white;
      padding: 10px;
      border-radius: var(--radius-sm);
      box-shadow: 0 10px 30px rgba(0,0,0,0.5);
      max-width: 96vw;
      max-height: 80vh;
      overflow: auto;
    }}

    .lightbox-img {{
      max-width: 90vw;
      max-height: 75vh;
      object-fit: contain;
      display: block;
      margin: auto;
    }}

    .lightbox-nav-btn {{
      position: absolute;
      top: 50%;
      transform: translateY(-50%);
      background: rgba(0, 0, 0, 0.65);
      border: 1px solid rgba(255, 255, 255, 0.35);
      color: white;
      width: 44px;
      height: 44px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 22px;
      cursor: pointer;
      transition: all 0.2s;
      z-index: 10;
      touch-action: manipulation;
    }}

    .lightbox-nav-btn:hover, .lightbox-nav-btn:active {{
      background: rgba(255, 255, 255, 0.35);
    }}

    .lightbox-nav-btn.prev {{ left: 14px; }}
    .lightbox-nav-btn.next {{ right: 14px; }}

    .lightbox-footer {{
      width: 100%;
      max-width: 1200px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      color: rgba(255, 255, 255, 0.7);
      font-size: 12px;
      gap: 8px;
    }}

    .empty-state {{
      text-align: center;
      padding: 50px 16px;
      color: var(--text-muted);
    }}

    .empty-state-icon {{
      font-size: 38px;
      margin-bottom: 10px;
    }}

    /* ========================================================
       RESPONSIVE BREAKPOINTS (TABLETS & PHONES)
       ======================================================== */
    @media (max-width: 900px) {{
      .grid-view {{
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
        gap: 14px;
      }}
    }}

    @media (max-width: 640px) {{
      .header-top {{
        padding: 10px 14px 6px;
      }}
      .header-title-text {{
        font-size: 17px;
      }}
      .control-bar {{
        padding: 4px 14px 10px;
        gap: 8px;
      }}
      .paper-picker-row {{
        flex-direction: column;
        align-items: stretch;
        gap: 8px;
      }}
      .paper-picker-top-subrow {{
        display: flex;
        align-items: center;
        gap: 8px;
        width: 100%;
      }}
      .select-wrapper {{
        flex: 1 1 auto;
        min-width: 0;
        width: 100%;
      }}
      .search-box {{
        width: 100%;
        flex: 1 1 auto;
      }}
      .exam-banner {{
        padding: 12px 14px;
      }}
      .banner-inner {{
        flex-direction: column;
        align-items: stretch;
        gap: 10px;
      }}
      .banner-info h2 {{
        font-size: 17px;
      }}
      .banner-stats {{
        width: 100%;
        justify-content: space-between;
      }}
      .stat-box {{
        flex: 1;
      }}
      .nav-bar-sticky {{
        padding: 8px 14px;
      }}
      .nav-bar-inner {{
        flex-direction: column;
        align-items: stretch;
        gap: 8px;
      }}
      .view-mode-toggle {{
        width: 100%;
      }}
      .view-btn {{
        flex: 1;
        text-align: center;
      }}
      .jump-palette-container {{
        padding: 0 14px;
      }}
      main.content-area {{
        padding: 0 14px;
        margin-top: 14px;
        margin-bottom: 40px;
      }}
      .grid-view {{
        grid-template-columns: 1fr;
        gap: 14px;
      }}
      .card-header {{
        padding: 8px 12px;
      }}
      .image-box {{
        padding: 8px;
        min-height: 90px;
      }}
      .card-footer {{
        padding: 6px 12px;
        font-size: 10px;
      }}
      .lightbox-modal {{
        padding: 10px 8px;
      }}
      .lightbox-nav-btn {{
        width: 38px;
        height: 38px;
        font-size: 18px;
      }}
      .lightbox-nav-btn.prev {{ left: 6px; }}
      .lightbox-nav-btn.next {{ right: 6px; }}
      .lightbox-footer {{
        flex-direction: column;
        gap: 2px;
        text-align: center;
        font-size: 11px;
      }}
      .lightbox-hint {{
        display: none;
      }}
    }}

    @media print {{
      header.portal-header,
      .control-bar,
      .category-chips,
      .nav-bar-sticky,
      .jump-palette-container,
      .card-header-actions,
      .card-footer,
      .lightbox-modal {{
        display: none !important;
      }}

      body {{
        background: #ffffff !important;
        color: #000000 !important;
      }}

      .grid-view {{
        display: block !important;
      }}

      .card {{
        break-inside: avoid;
        margin-bottom: 24px;
        box-shadow: none !important;
        border: 1px solid #cccccc !important;
      }}

      .image-box {{
        background: transparent !important;
      }}
    }}
  </style>
</head>
<body oncontextmenu="return false;" onselectstart="return false;" ondragstart="return false;" oncopy="return false;" oncut="return false;" onpaste="return false;">

  <!-- HEADER -->
  <header class="portal-header">
    <div class="header-top">
      <div class="header-title-text" id="topHeaderTitle">Question Papers</div>
      <div class="header-actions">
        <button class="btn btn-icon" id="themeToggleBtn" title="Toggle Light / Dark Mode">
          <span id="themeIcon">☀️</span>
        </button>
        <button class="btn" id="printBtn" title="Print Current Question Paper (PDF)">
          🖨️ Print
        </button>
      </div>
    </div>

    <div class="control-bar">
      <!-- Category Chips -->
      <div class="category-chips" id="categoryChips">
        <button class="category-chip active" data-cat="all">All ({len(paper_list)})</button>
        <button class="category-chip" data-cat="neet-11">11th NEET ({sum(1 for p in paper_list if p['category_key'] == 'neet-11')})</button>
        <button class="category-chip" data-cat="neet-12">12th NEET ({sum(1 for p in paper_list if p['category_key'] == 'neet-12')})</button>
        <button class="category-chip" data-cat="jee-11">11th JEE ({sum(1 for p in paper_list if p['category_key'] == 'jee-11')})</button>
        <button class="category-chip" data-cat="jee-12">12th JEE ({sum(1 for p in paper_list if p['category_key'] == 'jee-12')})</button>
        <button class="category-chip" data-cat="minor">Minor ({sum(1 for p in paper_list if p['category_key'] == 'minor')})</button>
        <button class="category-chip" data-cat="class-9">Class 9 ({sum(1 for p in paper_list if p['category_key'] == 'class-9')})</button>
        <button class="category-chip" data-cat="mock">Mock &amp; Demo ({sum(1 for p in paper_list if p['category_key'] == 'mock')})</button>
        <button class="category-chip" data-cat="mat">MAT ({sum(1 for p in paper_list if p['category_key'] == 'mat')})</button>
        <button class="category-chip" data-cat="topic-25">25Q Sets ({sum(1 for p in paper_list if p['category_key'] == 'topic-25')})</button>
        <button class="category-chip" data-cat="topic-20">20Q Sets ({sum(1 for p in paper_list if p['category_key'] == 'topic-20')})</button>
        <button class="category-chip" data-cat="practice">Practice ({sum(1 for p in paper_list if p['category_key'] == 'practice')})</button>
        <button class="category-chip" data-cat="screenshot">Screenshots ({sum(1 for p in paper_list if p['category_key'] == 'screenshot')})</button>
      </div>

      <!-- Paper Dropdown & Search -->
      <div class="paper-picker-row">
        <div class="paper-picker-top-subrow">
          <button class="btn btn-icon" id="prevPaperBtn" title="Previous Question Paper">◀</button>
          
          <div class="select-wrapper">
            <select id="paperSelect" class="paper-select">
              <!-- Populated dynamically via JS -->
            </select>
            <span class="select-chevron">▼</span>
          </div>

          <button class="btn btn-icon" id="nextPaperBtn" title="Next Question Paper">▶</button>
        </div>

        <div class="search-box">
          <span class="search-icon">🔍</span>
          <input type="text" id="searchInput" class="search-input" placeholder="Search Q# (e.g. 15)...">
        </div>
      </div>
    </div>
  </header>

  <!-- EXAM BANNER -->
  <section class="exam-banner">
    <div class="banner-inner">
      <div class="banner-info">
        <h2 id="paperTitle">
          <span id="paperTitleText">Loading...</span>
          <span id="paperBadge" class="badge">NEET</span>
        </h2>
        <div id="paperSubtitle" class="banner-subtitle">Please select a question paper</div>
      </div>
      <div class="banner-stats">
        <div class="stat-box">
          <div class="stat-value" id="statQuestions">0</div>
          <div class="stat-label">Questions</div>
        </div>
        <div class="stat-box">
          <div class="stat-value" id="statSubjects">0</div>
          <div class="stat-label">Sections</div>
        </div>
      </div>
    </div>
  </section>

  <!-- SUBJECT TABS & VIEW TOGGLE -->
  <nav class="nav-bar-sticky">
    <div class="nav-bar-inner">
      <div class="subject-tabs" id="subjectTabs">
        <!-- Subject tab buttons generated here -->
      </div>

      <div class="view-mode-toggle">
        <button class="view-btn active" id="viewGridBtn">Grid View</button>
        <button class="view-btn" id="viewFocusBtn">Single Question</button>
      </div>
    </div>
  </nav>

  <!-- JUMP NAVIGATOR PALETTE -->
  <div class="jump-palette-container" id="jumpPaletteContainer">
    <div class="jump-palette" id="jumpPalette">
      <div class="jump-label">Jump to Question:</div>
      <!-- Number pills generated here -->
    </div>
  </div>

  <!-- MAIN CONTENT AREA -->
  <main class="content-area">
    <div id="questionContainer" class="grid-view">
      <!-- Question cards injected here -->
    </div>
  </main>

  <!-- FULLSCREEN LIGHTBOX MODAL -->
  <div class="lightbox-modal" id="lightboxModal">
    <div class="lightbox-header">
      <div class="lightbox-title" id="lightboxTitle">Question Preview</div>
      <div class="lightbox-controls">
        <button class="lightbox-btn" id="zoomInBtn" title="Zoom In (+)">➕</button>
        <button class="lightbox-btn" id="zoomOutBtn" title="Zoom Out (-)">➖</button>
        <button class="lightbox-btn" id="rotateBtn" title="Rotate (90°)">↻</button>
        <button class="lightbox-btn" id="resetZoomBtn" title="Reset (100%)">1:1</button>
        <button class="lightbox-btn" id="lightboxCloseBtn">✖</button>
      </div>
    </div>

    <div class="lightbox-body" id="lightboxBody">
      <button class="lightbox-nav-btn prev" id="lightboxPrevBtn" title="Previous Question">❮</button>
      <div class="lightbox-img-wrapper" id="lightboxImgWrapper">
        <img src="" alt="Question Preview" id="lightboxImg" class="lightbox-img">
      </div>
      <button class="lightbox-nav-btn next" id="lightboxNextBtn" title="Next Question">❯</button>
    </div>

    <div class="lightbox-footer">
      <span id="lightboxSubject">Subject</span>
      <span id="lightboxIndex">Q1 / 25</span>
      <span class="lightbox-hint">Swipe ← / → on mobile or use arrow keys</span>
    </div>
  </div>

  <!-- SCRIPT DATA & APP LOGIC -->
  <script>
    const PAPERS_DATA = {data_json};

    let currentPaperIndex = 0;
    let currentSubjectCode = "all";
    let currentViewMode = "grid";
    let activeQuestions = [];
    let currentLightboxIdx = 0;
    let zoomLevel = 1;
    let rotationAngle = 0;

    const paperSelect = document.getElementById("paperSelect");
    const categoryChips = document.getElementById("categoryChips");
    const paperTitleText = document.getElementById("paperTitleText");
    const paperBadge = document.getElementById("paperBadge");
    const paperSubtitle = document.getElementById("paperSubtitle");
    const statQuestions = document.getElementById("statQuestions");
    const statSubjects = document.getElementById("statSubjects");
    const subjectTabs = document.getElementById("subjectTabs");
    const jumpPalette = document.getElementById("jumpPalette");
    const questionContainer = document.getElementById("questionContainer");
    const searchInput = document.getElementById("searchInput");
    const prevPaperBtn = document.getElementById("prevPaperBtn");
    const nextPaperBtn = document.getElementById("nextPaperBtn");
    const viewGridBtn = document.getElementById("viewGridBtn");
    const viewFocusBtn = document.getElementById("viewFocusBtn");
    const themeToggleBtn = document.getElementById("themeToggleBtn");
    const themeIcon = document.getElementById("themeIcon");
    const printBtn = document.getElementById("printBtn");

    const lightboxModal = document.getElementById("lightboxModal");
    const lightboxImg = document.getElementById("lightboxImg");
    const lightboxImgWrapper = document.getElementById("lightboxImgWrapper");
    const lightboxTitle = document.getElementById("lightboxTitle");
    const lightboxSubject = document.getElementById("lightboxSubject");
    const lightboxIndex = document.getElementById("lightboxIndex");
    const lightboxCloseBtn = document.getElementById("lightboxCloseBtn");
    const lightboxPrevBtn = document.getElementById("lightboxPrevBtn");
    const lightboxNextBtn = document.getElementById("lightboxNextBtn");
    const zoomInBtn = document.getElementById("zoomInBtn");
    const zoomOutBtn = document.getElementById("zoomOutBtn");
    const rotateBtn = document.getElementById("rotateBtn");
    const resetZoomBtn = document.getElementById("resetZoomBtn");

    /* ========================================================
       SECURITY & ANTI-INSPECTION DEVTOOLS LOCKS
       ======================================================== */
    document.addEventListener("contextmenu", (e) => e.preventDefault());
    document.addEventListener("dragstart", (e) => e.preventDefault());
    document.addEventListener("selectstart", (e) => e.preventDefault());
    document.addEventListener("copy", (e) => e.preventDefault());
    document.addEventListener("cut", (e) => e.preventDefault());

    window.addEventListener("keydown", (e) => {{
      if (e.keyCode === 123 || e.key === "F12") {{
        e.preventDefault();
        e.stopPropagation();
        return false;
      }}
      if ((e.ctrlKey || e.metaKey) && e.shiftKey && (e.key === "I" || e.key === "i" || e.key === "J" || e.key === "j" || e.key === "C" || e.key === "c")) {{
        e.preventDefault();
        e.stopPropagation();
        return false;
      }}
      if ((e.ctrlKey || e.metaKey) && (e.key === "U" || e.key === "u")) {{
        e.preventDefault();
        e.stopPropagation();
        return false;
      }}
      if ((e.ctrlKey || e.metaKey) && (e.key === "S" || e.key === "s")) {{
        e.preventDefault();
        e.stopPropagation();
        return false;
      }}
    }}, true);

    function populateDropdown(filterCategory = "all") {{
      paperSelect.innerHTML = "";
      
      const filtered = filterCategory === "all"
        ? PAPERS_DATA
        : PAPERS_DATA.filter(p => p.category_key === filterCategory);

      const groups = {{}};
      filtered.forEach((p) => {{
        const originalIndex = PAPERS_DATA.indexOf(p);
        if (!groups[p.category]) groups[p.category] = [];
        groups[p.category].push({{ paper: p, originalIndex }});
      }});

      for (const [catName, items] of Object.entries(groups)) {{
        const optgroup = document.createElement("optgroup");
        optgroup.label = `${{catName}} (${{items.length}})`;
        items.forEach(({{ paper, originalIndex }}) => {{
          const opt = document.createElement("option");
          opt.value = originalIndex;
          opt.textContent = `${{paper.title}} (${{paper.total_questions}}Q)`;
          optgroup.appendChild(opt);
        }});
        paperSelect.appendChild(optgroup);
      }}

      if (filtered.length > 0) {{
        const hasCurrent = filtered.some(p => PAPERS_DATA.indexOf(p) === currentPaperIndex);
        if (!hasCurrent) {{
          currentPaperIndex = PAPERS_DATA.indexOf(filtered[0]);
        }}
        paperSelect.value = currentPaperIndex;
      }}
    }}

    function renderCurrentPaper() {{
      const paper = PAPERS_DATA[currentPaperIndex];
      if (!paper) return;

      paperSelect.value = currentPaperIndex;
      paperTitleText.textContent = paper.title;
      paperBadge.className = `badge ${{paper.badge_class}}`;
      paperBadge.textContent = paper.category;
      paperSubtitle.textContent = paper.subtitle;
      statQuestions.textContent = paper.total_questions;
      statSubjects.textContent = paper.subjects.length;

      renderSubjectTabs(paper);
      renderQuestions();
    }}

    function renderSubjectTabs(paper) {{
      subjectTabs.innerHTML = "";

      if (paper.subjects.length > 1) {{
        const allBtn = document.createElement("button");
        allBtn.className = `tab-btn ${{currentSubjectCode === "all" ? "active" : ""}}`;
        allBtn.innerHTML = `All Subjects <span class="tab-count">${{paper.total_questions}}</span>`;
        allBtn.onclick = () => {{
          currentSubjectCode = "all";
          renderSubjectTabs(paper);
          renderQuestions();
        }};
        subjectTabs.appendChild(allBtn);
      }} else {{
        currentSubjectCode = paper.subjects[0].code;
      }}

      paper.subjects.forEach(sub => {{
        const btn = document.createElement("button");
        const isActive = currentSubjectCode === sub.code || (paper.subjects.length === 1);
        const subClass = `tab-${{sub.name.toLowerCase().replace(/[^a-z]/g, "")}}`;
        btn.className = `tab-btn ${{subClass}} ${{isActive ? "active" : ""}}`;
        btn.innerHTML = `${{sub.name}} <span class="tab-count">${{sub.count}}</span>`;
        btn.onclick = () => {{
          currentSubjectCode = sub.code;
          renderSubjectTabs(paper);
          renderQuestions();
        }};
        subjectTabs.appendChild(btn);
      }});
    }}

    function getActiveQuestionList() {{
      const paper = PAPERS_DATA[currentPaperIndex];
      if (!paper) return [];

      let list = [];
      if (currentSubjectCode === "all" || paper.subjects.length === 1) {{
        paper.subjects.forEach(sub => {{
          sub.questions.forEach(q => {{
            list.push({{ ...q, subjectName: sub.name }});
          }});
        }});
      }} else {{
        const sub = paper.subjects.find(s => s.code === currentSubjectCode);
        if (sub) {{
          sub.questions.forEach(q => {{
            list.push({{ ...q, subjectName: sub.name }});
          }});
        }}
      }}
      return list;
    }}

    function renderQuestions(filterText = "") {{
      activeQuestions = getActiveQuestionList();

      if (filterText.trim()) {{
        const query = filterText.trim().toLowerCase().replace(/^q/, '');
        activeQuestions = activeQuestions.filter(q => 
          String(q.num).includes(query) ||
          q.filename.toLowerCase().includes(query)
        );
      }}

      jumpPalette.innerHTML = '<div class="jump-label">Jump to Question:</div>';
      activeQuestions.forEach((q, idx) => {{
        const pill = document.createElement("a");
        pill.className = "jump-pill";
        pill.textContent = q.num;
        pill.title = `Question ${{q.num}}`;
        pill.href = `#card-${{idx}}`;
        pill.onclick = (e) => {{
          e.preventDefault();
          const targetCard = document.getElementById(`card-${{idx}}`);
          if (targetCard) {{
            targetCard.scrollIntoView({{ behavior: "smooth", block: "center" }});
            targetCard.classList.add("highlighted");
            setTimeout(() => targetCard.classList.remove("highlighted"), 1800);
          }}
        }};
        jumpPalette.appendChild(pill);
      }});

      questionContainer.className = currentViewMode === "grid" ? "grid-view" : "focus-view";
      questionContainer.innerHTML = "";

      if (activeQuestions.length === 0) {{
        questionContainer.innerHTML = `
          <div class="empty-state">
            <div class="empty-state-icon">🔍</div>
            <h3>No questions found</h3>
            <p>Try clearing your search query or switching subject tabs.</p>
          </div>
        `;
        return;
      }}

      activeQuestions.forEach((q, idx) => {{
        const card = document.createElement("div");
        card.className = "card";
        card.id = `card-${{idx}}`;

        card.innerHTML = `
          <div class="card-header">
            <div class="card-header-title">
              <span class="q-number">Question ${{q.num}}</span>
              <span class="q-subject-tag">${{q.subjectName}}</span>
            </div>
            <div class="card-header-actions">
              <button class="card-btn zoom-btn" title="Fullscreen Zoom">🔍 Zoom</button>
            </div>
          </div>
          <div class="image-box" title="Tap to open fullscreen">
            <img class="question-img" draggable="false" oncontextmenu="return false;" ondragstart="return false;" src="${{q.url}}" alt="Question ${{q.num}}" loading="lazy" />
          </div>
          <div class="card-footer">
            <span>${{q.filename}}</span>
            <span>#${{idx + 1}} of ${{activeQuestions.length}}</span>
          </div>
        `;

        const imgBox = card.querySelector(".image-box");
        const zoomBtn = card.querySelector(".zoom-btn");
        const openLightbox = () => openModal(idx);
        imgBox.onclick = openLightbox;
        zoomBtn.onclick = openLightbox;

        questionContainer.appendChild(card);
      }});
    }}

    function openModal(idx) {{
      if (idx < 0 || idx >= activeQuestions.length) return;
      currentLightboxIdx = idx;
      zoomLevel = 1;
      rotationAngle = 0;
      updateModalImage();
      lightboxModal.classList.add("active");
      document.body.style.overflow = "hidden";
    }}

    function closeModal() {{
      lightboxModal.classList.remove("active");
      document.body.style.overflow = "";
    }}

    function updateModalImage() {{
      const q = activeQuestions[currentLightboxIdx];
      if (!q) return;

      lightboxImg.src = q.url;
      lightboxTitle.textContent = `Question ${{q.num}}`;
      lightboxSubject.textContent = `${{q.subjectName}} • ${{q.filename}}`;
      lightboxIndex.textContent = `Question ${{currentLightboxIdx + 1}} of ${{activeQuestions.length}}`;

      applyTransform();
    }}

    function applyTransform() {{
      lightboxImgWrapper.style.transform = `scale(${{zoomLevel}}) rotate(${{rotationAngle}}deg)`;
    }}

    function nextQuestion() {{
      if (currentLightboxIdx < activeQuestions.length - 1) {{
        currentLightboxIdx++;
        updateModalImage();
      }}
    }}

    function prevQuestion() {{
      if (currentLightboxIdx > 0) {{
        currentLightboxIdx--;
        updateModalImage();
      }}
    }}

    // Touch Swipe Gestures for Mobile Lightbox Navigation
    let touchStartX = 0;
    let touchStartY = 0;
    lightboxModal.addEventListener("touchstart", (e) => {{
      if (e.touches && e.touches.length === 1) {{
        touchStartX = e.touches[0].clientX;
        touchStartY = e.touches[0].clientY;
      }}
    }}, {{ passive: true }});

    lightboxModal.addEventListener("touchend", (e) => {{
      if (e.changedTouches && e.changedTouches.length === 1) {{
        const diffX = e.changedTouches[0].clientX - touchStartX;
        const diffY = e.changedTouches[0].clientY - touchStartY;
        // Only trigger swipe if horizontal swipe is prominent and zoom is default
        if (zoomLevel === 1 && Math.abs(diffX) > 45 && Math.abs(diffY) < 65) {{
          if (diffX < 0) nextQuestion();
          else prevQuestion();
        }}
      }}
    }}, {{ passive: true }});

    paperSelect.onchange = (e) => {{
      currentPaperIndex = parseInt(e.target.value, 10);
      currentSubjectCode = "all";
      searchInput.value = "";
      renderCurrentPaper();
      window.scrollTo({{ top: 0, behavior: "smooth" }});
    }};

    prevPaperBtn.onclick = () => {{
      if (currentPaperIndex > 0) {{
        currentPaperIndex--;
        currentSubjectCode = "all";
        searchInput.value = "";
        renderCurrentPaper();
        window.scrollTo({{ top: 0, behavior: "smooth" }});
      }}
    }};

    nextPaperBtn.onclick = () => {{
      if (currentPaperIndex < PAPERS_DATA.length - 1) {{
        currentPaperIndex++;
        currentSubjectCode = "all";
        searchInput.value = "";
        renderCurrentPaper();
        window.scrollTo({{ top: 0, behavior: "smooth" }});
      }}
    }};

    categoryChips.addEventListener("click", (e) => {{
      const chip = e.target.closest(".category-chip");
      if (!chip) return;

      categoryChips.querySelectorAll(".category-chip").forEach(c => c.classList.remove("active"));
      chip.classList.add("active");

      const cat = chip.dataset.cat;
      populateDropdown(cat);
      renderCurrentPaper();
    }});

    searchInput.addEventListener("input", (e) => {{
      renderQuestions(e.target.value);
    }});

    viewGridBtn.onclick = () => {{
      currentViewMode = "grid";
      viewGridBtn.classList.add("active");
      viewFocusBtn.classList.remove("active");
      questionContainer.className = "grid-view";
    }};

    viewFocusBtn.onclick = () => {{
      currentViewMode = "focus";
      viewFocusBtn.classList.add("active");
      viewGridBtn.classList.remove("active");
      questionContainer.className = "focus-view";
    }};

    lightboxCloseBtn.onclick = closeModal;
    lightboxPrevBtn.onclick = prevQuestion;
    lightboxNextBtn.onclick = nextQuestion;

    zoomInBtn.onclick = () => {{
      zoomLevel = Math.min(zoomLevel + 0.25, 3.5);
      applyTransform();
    }};

    zoomOutBtn.onclick = () => {{
      zoomLevel = Math.max(zoomLevel - 0.25, 0.5);
      applyTransform();
    }};

    rotateBtn.onclick = () => {{
      rotationAngle = (rotationAngle + 90) % 360;
      applyTransform();
    }};

    resetZoomBtn.onclick = () => {{
      zoomLevel = 1;
      rotationAngle = 0;
      applyTransform();
    }};

    document.addEventListener("keydown", (e) => {{
      if (lightboxModal.classList.contains("active")) {{
        if (e.key === "Escape") closeModal();
        if (e.key === "ArrowLeft") prevQuestion();
        if (e.key === "ArrowRight") nextQuestion();
        if (e.key === "+" || e.key === "=") {{
          zoomLevel = Math.min(zoomLevel + 0.25, 3.5);
          applyTransform();
        }}
        if (e.key === "-") {{
          zoomLevel = Math.max(zoomLevel - 0.25, 0.5);
          applyTransform();
        }}
      }}
    }});

    themeToggleBtn.onclick = () => {{
      const currentTheme = document.documentElement.getAttribute("data-theme") || "dark";
      const newTheme = currentTheme === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", newTheme);
      themeIcon.textContent = newTheme === "dark" ? "☀️" : "🌙";
      localStorage.setItem("qp_portal_theme", newTheme);
    }};

    const savedTheme = localStorage.getItem("qp_portal_theme") || "dark";
    document.documentElement.setAttribute("data-theme", savedTheme);
    themeIcon.textContent = savedTheme === "dark" ? "☀️" : "🌙";

    printBtn.onclick = () => {{
      window.print();
    }};

    populateDropdown("all");
    renderCurrentPaper();
  </script>
</body>
</html>
'''

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_template)

print("Updated index.html with responsive mobile layout & swipe gestures!")
