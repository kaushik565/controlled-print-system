import re

tests = [
    "Page 04 of 08 and 05 of 08 09 copies",
    "PAGE 05OF 08 TO 06 OF 08   09 COPYS",
    "PAGE 07 OF 14  TO PAGE 11 OF 14    19 COPY",
    "PAGE 01 of 04 to 02 of 04 1 COPY",
    "05 COPY",
    "10"
]

def parse(line):
    # Find all page numbers. We want to catch things like "Page 4" or "04 of 08"
    # Wait, the structure is typically:
    # (Page)? \d+ (of \d+)? (to|and|-) (Page)? \d+ (of \d+)?  [...copies]
    
    # Let's extract all page numbers first by stripping out "of \d+"
    # Replace "of \d+" with nothing
    clean_line = re.sub(r'(?i)\s*of\s*\d+', '', line)
    
    # Now clean_line might look like:
    # "Page 04 and 05 09 copies"
    # "PAGE 05 TO 06   09 COPYS"
    # "PAGE 07  TO PAGE 11    19 COPY"
    
    # Find ranges: (\d+)\s*(?:to|-|and)\s*(?:page\s*)?(\d+)
    ranges = []
    
    # We can just look for "copies" number at the end
    copies = None
    m_copies = re.search(r'(\d+)\s*cop', clean_line, re.IGNORECASE)
    if m_copies:
        copies = int(m_copies.group(1))
        clean_line = clean_line[:m_copies.start()]
    else:
        # Check if just a number
        m_num = re.search(r'\s*(\d+)\s*$', clean_line)
        if m_num:
            copies = int(m_num.group(1))
            clean_line = clean_line[:m_num.start()]
            
    # Now extract pages from the remaining clean_line
    # find all numbers in the clean line
    nums = [int(x) for x in re.findall(r'\d+', clean_line)]
    
    # check for "to" or "-" to indicate range
    pages = []
    if re.search(r'(?i)\bto\b|-', clean_line) and len(nums) >= 2:
        start = nums[0]
        end = nums[-1]
        pages = list(range(start, end + 1))
    elif re.search(r'(?i)\band\b', clean_line) and len(nums) >= 2:
        pages = nums
    elif len(nums) > 0:
        pages = nums
        
    return pages, copies
    
for t in tests:
    print(f"{t} -> {parse(t)}")
