import re

# Read file
for enc in ['utf-8', 'cp1252', 'latin-1']:
    try:
        with open(r'c:\Users\MJ\Desktop\Agric\apps\public-website\src\styles.css', 'r', encoding=enc) as f:
            content = f.read()
        break
    except Exception as e:
        print(f'Failed {enc}: {e}')
        continue

# Define replacements: old -> new
replacements = {
    'padding: 44px 40px': 'padding: 24px 20px',
    'padding: 40px': 'padding: 24px',
    'padding: 36px': 'padding: 20px',
    'padding: 32px': 'padding: 18px',
    'padding: 28px': 'padding: 16px',
    'padding: 24px': 'padding: 14px',
    'padding: 22px': 'padding: 14px',
    'padding: 20px': 'padding: 12px',
    'padding: 18px': 'padding: 12px',
    'padding: 16px': 'padding: 10px',
    'padding: 14px': 'padding: 10px',
    'padding: 12px': 'padding: 8px',
    'padding: 10px': 'padding: 6px',
    'gap: 32px': 'gap: 18px',
    'gap: 28px': 'gap: 16px',
    'gap: 24px': 'gap: 14px',
    'gap: 20px': 'gap: 12px',
    'gap: 16px': 'gap: 10px',
    'gap: 14px': 'gap: 10px',
    'gap: 12px': 'gap: 8px',
    'margin-bottom: 36px': 'margin-bottom: 20px',
    'margin-bottom: 32px': 'margin-bottom: 18px',
    'margin-bottom: 28px': 'margin-bottom: 16px',
    'margin-bottom: 24px': 'margin-bottom: 14px',
    'margin-bottom: 20px': 'margin-bottom: 12px',
    'margin-bottom: 16px': 'margin-bottom: 10px',
    'margin-bottom: 14px': 'margin-bottom: 10px',
    'margin-bottom: 12px': 'margin-bottom: 8px',
    'margin-bottom: 10px': 'margin-bottom: 6px',
    'margin-top: 32px': 'margin-top: 18px',
    'margin-top: 28px': 'margin-top: 16px',
    'margin-top: 24px': 'margin-top: 14px',
    'margin-top: 20px': 'margin-top: 12px',
    'margin-top: 16px': 'margin-top: 10px',
    'margin-top: 12px': 'margin-top: 8px',
    'border-radius: 24px': 'border-radius: 14px',
    'border-radius: 20px': 'border-radius: 12px',
    'border-radius: 18px': 'border-radius: 12px',
    'border-radius: 16px': 'border-radius: 10px',
    'border-radius: 14px': 'border-radius: 10px',
    'border-radius: 12px': 'border-radius: 8px',
    'font-size: 18px': 'font-size: 15px',
    'font-size: 16px': 'font-size: 14px',
    'font-size: 15px': 'font-size: 13px',
    'font-size: 14px': 'font-size: 12px',
    'font-size: 13px': 'font-size: 11px',
    'width: 40px; height: 40px': 'width: 28px; height: 28px',
    'width: 36px; height: 36px': 'width: 26px; height: 26px',
    'width: 32px; height: 32px': 'width: 24px; height: 24px',
    'padding: 80px 0': 'padding: 40px 0',
    'padding: 64px 0': 'padding: 36px 0',
    'padding: 48px 0': 'padding: 28px 0',
    'padding: 32px 0': 'padding: 20px 0',
}

# Sort by length descending to avoid partial replacements
for old, new in sorted(replacements.items(), key=lambda x: -len(x[0])):
    content = content.replace(old, new)

# Write back
for enc in ['utf-8', 'cp1252', 'latin-1']:
    try:
        with open(r'c:\Users\MJ\Desktop\Agric\apps\public-website\src\styles.css', 'w', encoding=enc) as f:
            f.write(content)
        print('Done')
        break
    except Exception as e:
        print(f'Write failed {enc}: {e}')
