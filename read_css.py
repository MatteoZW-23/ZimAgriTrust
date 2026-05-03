import sys
for enc in ['utf-8','latin-1','cp1252']:
    try:
        with open(r'c:\Users\MJ\Desktop\Agric\apps\public-website\src\styles.css','r',encoding=enc) as f:
            lines = f.readlines()
        for i,line in enumerate(lines[:80]):
            print(f'{i+1:3d}|{line.rstrip()}')
        sys.exit(0)
    except Exception as e:
        print(f'Failed {enc}: {e}')
