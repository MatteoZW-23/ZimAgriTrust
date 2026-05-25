"""Replace emoji crop icons with Lucide React icons in App.tsx MarketplaceSection."""
import pathlib, re

p = pathlib.Path(r"c:\Users\MJ\Desktop\Agric\apps\public-website\src\App.tsx")
content = p.read_text(encoding="utf-8")

# 1. Replace the cropEmoji line with a cropIcon function
lines = content.split("\n")
new_lines = []
for line in lines:
    if "cropEmoji: Record<string, string>" in line:
        new_lines.append("  const cropIcon = (name: string) => {")
        new_lines.append("    const key = (name || '').toLowerCase();")
        new_lines.append('    if (key.includes("maize") || key.includes("wheat") || key.includes("sorghum")) return <Wheat className="w-8 h-8 text-primary-600" />;')
        new_lines.append('    if (key.includes("soybean") || key.includes("groundnut") || key.includes("bean")) return <Sprout className="w-8 h-8 text-primary-600" />;')
        new_lines.append('    if (key.includes("tobacco") || key.includes("cotton")) return <Leaf className="w-8 h-8 text-primary-600" />;')
        new_lines.append('    if (key.includes("sunflower")) return <Sun className="w-8 h-8 text-primary-600" />;')
        new_lines.append('    return <Package className="w-8 h-8 text-primary-600" />;')
        new_lines.append("  };")
    else:
        new_lines.append(line)

content = "\n".join(new_lines)

# 2. Replace the emoji render: <span className="text-5xl">{cropEmoji[...] || "..."}</span>
#    with: <div className="w-12 h-12 ...">icon</div>
content = re.sub(
    r'<span className="text-5xl">\{cropEmoji\[.*?\]\s*\|\|\s*"[^"]*"\}</span>',
    '<div className="w-12 h-12 rounded-xl bg-primary-50 flex items-center justify-center">{cropIcon(crop.commodity || crop.product_type || "")}</div>',
    content,
)

p.write_text(content, encoding="utf-8")
print("Done — emojis replaced with Lucide icons")
