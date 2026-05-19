import SwiftUI
import VisionKit

struct DocumentScannerView: View {
    @StateObject private var scanner = DocumentScanner()
    @State private var selectedDocumentType: DocumentType = .nationalID
    @State private var processedData: IDDocumentData?
    @State private var showResults = false
    @State private var isProcessing = false
    
    enum DocumentType: String, CaseIterable {
        case nationalID = "National ID"
        case passport = "Passport"
        case driversLicense = "Driver's License"
    }
    
    var body: some View {
        NavigationView {
            VStack(spacing: 20) {
                // Document Type Selection
                Picker("Document Type", selection: $selectedDocumentType) {
                    ForEach(DocumentType.allCases, id: \.self) { type in
                        Text(type.rawValue).tag(type)
                    }
                }
                .pickerStyle(SegmentedPickerStyle())
                .padding()
                
                // Scanner Button
                Button(action: {
                    // This would be called from a parent view controller
                    scanner.errorMessage = "Please present this view from a UIViewController"
                }) {
                    VStack {
                        Image(systemName: "doc.text.viewfinder")
                            .font(.system(size: 60))
                            .foregroundColor(.blue)
                        
                        Text("Scan Document")
                            .font(.headline)
                            .foregroundColor(.white)
                    }
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(Color.blue)
                    .cornerRadius(12)
                }
                .padding()
                
                // Scanned Images Preview
                if !scanner.scannedImages.isEmpty {
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 10) {
                            ForEach(0..<scanner.scannedImages.count, id: \.self) { index in
                                Image(uiImage: scanner.scannedImages[index])
                                    .resizable()
                                    .scaledToFit()
                                    .frame(height: 150)
                                    .cornerRadius(8)
                            }
                        }
                        .padding()
                    }
                    
                    Button("Process Document") {
                        processDocument()
                    }
                    .buttonStyle(.borderedProminent)
                    .padding()
                }
                
                // Error Message
                if let error = scanner.errorMessage {
                    Text(error)
                        .foregroundColor(.red)
                        .padding()
                }
                
                Spacer()
            }
            .navigationTitle("ID Verification")
            .alert("Document Data", isPresented: $showResults) {
                Button("OK", role: .cancel) { }
            } message: {
                if let data = processedData {
                    VStack(alignment: .leading, spacing: 8) {
                        if let idNumber = data.idNumber {
                            Text("ID Number: \(idNumber)")
                        }
                        if let name = data.fullName {
                            Text("Name: \(name)")
                        }
                        if let dob = data.dateOfBirth {
                            Text("Date of Birth: \(dob)")
                        }
                    }
                }
            }
        }
    }
    
    private func processDocument() {
        guard let firstImage = scanner.scannedImages.first else { return }
        
        isProcessing = true
        
        Task {
            do {
                let cropped = try await scanner.cropDocumentFromImage(image: firstImage)
                let data = try await scanner.processIDDocument(image: cropped)
                
                await MainActor.run {
                    self.processedData = data
                    self.isProcessing = false
                    self.showResults = true
                }
            } catch {
                await MainActor.run {
                    self.scanner.errorMessage = error.localizedDescription
                    self.isProcessing = false
                }
            }
        }
    }
}

#Preview {
    DocumentScannerView()
}
