import SwiftUI
import PencilKit

struct SignatureView: View {
    @StateObject private var signatureManager = SignatureManager()
    @State private var showSignatureCanvas = false
    @State private var showSavedSignature = false
    
    let onSave: (Data) -> Void
    let onCancel: () -> Void
    
    var body: some View {
        NavigationView {
            VStack(spacing: 20) {
                // Instructions
                VStack(alignment: .leading, spacing: 8) {
                    Text("Please sign below")
                        .font(.headline)
                    Text("Use your finger or Apple Pencil to sign")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding()
                
                // Signature Canvas
                ZStack {
                    if showSignatureCanvas {
                        SignatureCanvasRepresentable(signatureManager: signatureManager)
                            .frame(height: 200)
                            .cornerRadius(12)
                            .overlay(
                                RoundedRectangle(cornerRadius: 12)
                                    .stroke(Color.gray, lineWidth: 1)
                            )
                    } else {
                        Rectangle()
                            .fill(Color.gray.opacity(0.1))
                            .frame(height: 200)
                            .cornerRadius(12)
                            .overlay(
                                VStack {
                                    Image(systemName: "pencil")
                                        .font(.system(size: 40))
                                        .foregroundColor(.gray)
                                    Text("Tap to sign")
                                        .foregroundColor(.gray)
                                }
                            )
                            .onTapGesture {
                                showSignatureCanvas = true
                            }
                    }
                }
                .padding()
                
                // Signature Preview
                if let signatureImage = signatureManager.signatureImage {
                    VStack {
                        Text("Signature Preview")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        
                        Image(uiImage: signatureImage)
                            .resizable()
                            .scaledToFit()
                            .frame(height: 100)
                            .background(Color.white)
                            .cornerRadius(8)
                            .shadow(radius: 2)
                    }
                    .padding()
                }
                
                // Action Buttons
                HStack(spacing: 16) {
                    Button("Clear") {
                        signatureManager.clearSignature()
                        showSignatureCanvas = false
                    }
                    .buttonStyle(.bordered)
                    .disabled(!signatureManager.hasSignature)
                    
                    Spacer()
                    
                    Button("Cancel") {
                        onCancel()
                    }
                    .buttonStyle(.bordered)
                    
                    Button("Save") {
                        if let data = signatureManager.signatureData {
                            onSave(data)
                        }
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(!signatureManager.hasSignature || !signatureManager.validateSignature())
                }
                .padding()
                
                Spacer()
            }
            .navigationTitle("Signature")
            .navigationBarTitleDisplayMode(.inline)
        }
    }
}

struct SignatureCanvasRepresentable: UIViewRepresentable {
    @ObservedObject var signatureManager: SignatureManager
    
    func makeUIView(context: Context) -> SignatureCanvasView {
        let canvasView = signatureManager.createSignatureView()
        return canvasView
    }
    
    func updateUIView(_ uiView: SignatureCanvasView, context: Context) {
        // Update view if needed
    }
}

#Preview {
    SignatureView(
        onSave: { _ in print("Saved") },
        onCancel: { print("Cancelled") }
    )
}
