import os
import json

def seed():
    print("🚀 Seeding AgriTrust Sovereign Agent Academy...")
    
    base_dir = "agent_training_materials"
    modules = [
        "Platform_Sovereignty", "Escrow_Governance", "Field_Verification", 
        "Dispute_Resolution", "Trust_Metrics", "Marketplace_Ethics",
        "Rural_Finance", "Legal_Framework", "Advanced_Technology", "Customer_Excellence"
    ]
    
    for i, name in enumerate(modules, 1):
        module_dir = os.path.join(base_dir, f"module_{i}_{name.lower()}")
        os.makedirs(module_dir, exist_ok=True)
        
        # Create Handbook Stub
        with open(os.path.join(module_dir, f"handbook_m{i}.txt"), "w") as f:
            f.write(f"AgriTrust Module {i}: {name}\n" + "="*40 + "\n\nThis document contains 64 pages of proprietary operational protocol...")

        # Create Module Quiz
        quiz = {
            "module_id": i,
            "questions": [
                {
                    "q": f"What is the key principle of {name}?",
                    "options": ["Sovereignty", "Centralization", "Opaque Trade", "Manual Ledger"],
                    "a": "Sovereignty"
                }
            ]
        }
        with open(os.path.join(module_dir, f"quiz_m{i}.json"), "w") as f:
            json.dump(quiz, f, indent=2)
            
    print("✅ All 10 modules seeded. Curriculum is now live.")

if __name__ == "__main__":
    seed()
