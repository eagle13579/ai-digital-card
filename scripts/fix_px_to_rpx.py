"""
AI数字名片 — 小程序 wxss px→rpx 批量转换脚本
============================================
规则:
  1px = 2rpx (基于375设计稿)
  转换属性: width,height,padding,margin,font-size,border-radius,top,left,right,bottom,gap,flex-basis,line-height(带px)
  保留属性: border, box-shadow, text-shadow, transform, outline (这些不影响布局缩放)
"""
import re, os

MINIAPP = "D:/AI数智名片/miniapp"

# CSS属性 → 转换策略
CONVERT_PROPS = {
    'width', 'height', 'min-width', 'min-height', 'max-width', 'max-height',
    'padding', 'padding-top', 'padding-right', 'padding-bottom', 'padding-left',
    'margin', 'margin-top', 'margin-right', 'margin-bottom', 'margin-left',
    'font-size', 'line-height', 'letter-spacing',
    'border-radius', 'border-top-left-radius', 'border-top-right-radius',
    'border-bottom-left-radius', 'border-bottom-right-radius',
    'top', 'left', 'right', 'bottom',
    'gap', 'row-gap', 'column-gap', 'flex-basis',
    'text-indent', 'border-width', 'border-top-width', 'border-right-width',
    'border-bottom-width', 'border-left-width',
    'outline-offset', 'transform-origin',
}

KEEP_PROPS = {'border', 'box-shadow', 'text-shadow', 'outline', 'transform'}

def convert_px_to_rpx(css_text):
    """Convert px values in CSS properties to rpx (multiply by 2)"""
    
    def replace_px(match):
        prop = match.group(1).strip()
        value = match.group(2)
        num_str = match.group(3)
        
        # Skip non-convertible properties
        if prop in KEEP_PROPS:
            return match.group(0)
        
        # Only convert if property is in CONVERT_PROPS or is a generic size property
        should_convert = prop in CONVERT_PROPS
        
        if not should_convert:
            return match.group(0)
        
        try:
            num = float(num_str)
            rpx_val = num * 2
            # Round to integer for clean CSS
            if rpx_val == int(rpx_val):
                return f"{prop}: {int(rpx_val)}rpx"
            else:
                return f"{prop}: {rpx_val:.1f}rpx"
        except ValueError:
            return match.group(0)
    
    # Pattern: property: valuepx  (e.g., "width: 100px")
    pattern = r'([a-z-]+):\s*(-?\d+(?:\.\d+)?)px'
    result = re.sub(pattern, replace_px, css_text)
    return result

# Also fix inline style attributes in wxml
def convert_wxml_inline_styles(wxml_text):
    """Convert inline style px values in wxml"""
    
    def fix_style_value(match):
        full = match.group(0)
        # Don't touch styles that contain border/box-shadow/transform
        if 'border' in full and 'border-radius' not in full:
            return full
        if 'box-shadow' in full or 'text-shadow' in full:
            return full
        
        def replace_num(m):
            try:
                num = float(m.group(1))
                return f"{int(num * 2)}rpx" if num * 2 == int(num * 2) else f"{num * 2:.1f}rpx"
            except:
                return m.group(0)
        
        return re.sub(r'(\d+(?:\.\d+)?)(?=px)', replace_num, full)
    
    # Match style="..." attributes
    return re.sub(r'style="([^"]*)"', lambda m: f'style="{fix_style_value(m.group(1))}"', wxml_text)

# Process all wxss files
total_px = 0
total_converted = 0
converted_files = []

for root, dirs, files in os.walk(MINIAPP):
    for f in files:
        if f.endswith('.wxss'):
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8') as fh:
                orig = fh.read()
            converted = convert_px_to_rpx(orig)
            px_count_before = len(re.findall(r'(\d+(?:\.\d+)?)px', orig))
            px_count_after = len(re.findall(r'(\d+(?:\.\d+)?)px', converted))
            converted_count = px_count_before - px_count_after
            if converted_count > 0:
                with open(path, 'w', encoding='utf-8') as fh:
                    fh.write(converted)
                total_px += px_count_before
                total_converted += converted_count
                converted_files.append((path[len(MINIAPP):], px_count_before, px_count_after, converted_count))
                print(f"  {path[len(MINIAPP):]}: {px_count_before}px → {px_count_after}px (-{converted_count})")

# Process wxml inline styles
for root, dirs, files in os.walk(MINIAPP):
    for f in files:
        if f.endswith('.wxml'):
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8') as fh:
                orig = fh.read()
            if 'px' in orig:
                converted = convert_wxml_inline_styles(orig)
                if converted != orig:
                    with open(path, 'w', encoding='utf-8') as fh:
                        fh.write(converted)
                    print(f"  [wxml] {path[len(MINIAPP):]}: inline px fixed")

print(f"\n✅ 总计: {len(converted_files)}个文件, {total_converted}/{total_px} px → rpx")
