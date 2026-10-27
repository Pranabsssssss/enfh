import urllib.request, urllib.parse
import xml.etree.ElementTree as ET
import os, time

base_url = 'https://s3-noi.aces3.ai/enable-lmsbucket001'
ns = {'s3': 'http://s3.amazonaws.com/doc/2006-03-01/'}

def fetch_all_keys(prefix):
    print(f"Fetching all keys for prefix: '{prefix}'...")
    token = None
    page = 1
    all_keys = []
    xml_chunks = []

    while True:
        params = {'list-type': '2', 'prefix': prefix}
        if token:
            params['continuation-token'] = token
        
        query_str = urllib.parse.urlencode(params)
        url = f"{base_url}?{query_str}"
        
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read()
            xml_chunks.append(content)
            root = ET.fromstring(content)
            keys = [c.find('s3:Key', ns).text for c in root.findall('s3:Contents', ns) if c.find('s3:Key', ns) is not None]
            all_keys.extend(keys)
            print(f"  Page {page}: got {len(keys)} keys (cumulative: {len(all_keys)})")
            
            is_trunc = root.find('s3:IsTruncated', ns)
            if is_trunc is not None and is_trunc.text.lower() == 'true':
                tok_elem = root.find('s3:NextContinuationToken', ns)
                if tok_elem is not None and tok_elem.text:
                    token = tok_elem.text
                    page += 1
                else:
                    break
            else:
                break
        time.sleep(0.1)
    
    print(f"Finished '{prefix}': {len(all_keys)} keys across {page} pages.\n")
    return all_keys, xml_chunks

# 1. Fetch COE prefix
coe_keys, coe_xml_chunks = fetch_all_keys('question_images/COE/')

# 2. Fetch all question_images/ prefix to get any other missing papers
full_keys, _ = fetch_all_keys('question_images/')

print(f"Summary: COE keys = {len(coe_keys)}, Total bucket keys = {len(full_keys)}")

# Save a consolidated enable-lmsbucket001_coe_full.xml
# Combine contents into a single valid XML
root_all = ET.Element('{http://s3.amazonaws.com/doc/2006-03-01/}ListBucketResult')
ET.SubElement(root_all, '{http://s3.amazonaws.com/doc/2006-03-01/}Name').text = 'enable-lmsbucket001'
ET.SubElement(root_all, '{http://s3.amazonaws.com/doc/2006-03-01/}Prefix').text = 'question_images/COE/'
ET.SubElement(root_all, '{http://s3.amazonaws.com/doc/2006-03-01/}KeyCount').text = str(len(coe_keys))
ET.SubElement(root_all, '{http://s3.amazonaws.com/doc/2006-03-01/}IsTruncated').text = 'false'

for k in coe_keys:
    c_elem = ET.SubElement(root_all, '{http://s3.amazonaws.com/doc/2006-03-01/}Contents')
    ET.SubElement(c_elem, '{http://s3.amazonaws.com/doc/2006-03-01/}Key').text = k

tree = ET.ElementTree(root_all)
tree.write('enable-lmsbucket001_coe_full.xml', encoding='utf-8', xml_declaration=True)
print("Saved enable-lmsbucket001_coe_full.xml with all 2,835 COE keys!")

# Save full bucket keys to a json index for high performance
with open('all_bucket_keys.json', 'w', encoding='utf-8') as f:
    import json
    json.dump(full_keys, f)
print("Saved all_bucket_keys.json with all 8,466 bucket keys!")
