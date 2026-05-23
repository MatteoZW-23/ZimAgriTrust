import Foundation
import VisionKit
import Vision
import UIKit

@MainActor
class DocumentScanner: NSObject, ObservableObject {
    @Published var scannedImages: [UIImage] = []
    @Published var isScanning = false
    @Published var errorMessage: String?
    
    private var documentScanViewController: VNDocumentCameraViewController?
    weak var presentingViewController: UIViewController?
    
    override init() {
        super.init()
    }
    
    func startScanning(from viewController: UIViewController) {
        guard VNDocumentCameraViewController.isSupported else {
            errorMessage = "Document scanning is not supported on this device"
            return
        }
        
        documentScanViewController = VNDocumentCameraViewController()
        documentScanViewController?.delegate = self
        presentingViewController = viewController
        
        viewController.present(documentScanViewController!, animated: true)
    }
    
    func processIDDocument(image: UIImage) async throws -> IDDocumentData {
        guard let cgImage = image.cgImage else {
            throw ScannerError.invalidImage
        }
        
        // OCR to extract text
        let request = VNRecognizeTextRequest()
        request.recognitionLevel = .accurate
        request.usesLanguageCorrection = true
        request.recognitionLanguages = ["en-US"]
        
        let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
        try handler.perform([request])
        
        guard let observations = request.results, !observations.isEmpty else {
            throw ScannerError.noTextFound
        }
        
        let recognizedText = observations.compactMap { $0.topCandidates(1).first?.string }.joined(separator: "\n")
        
        // Extract ID information using regex patterns
        let idNumber = extractIDNumber(from: recognizedText)
        let name = extractName(from: recognizedText)
        let dateOfBirth = extractDateOfBirth(from: recognizedText)
        
        return IDDocumentData(
            idNumber: idNumber,
            fullName: name,
            dateOfBirth: dateOfBirth,
            rawText: recognizedText,
            image: image
        )
    }
    
    func detectFaceInDocument(image: UIImage) async throws -> Bool {
        guard let cgImage = image.cgImage else {
            throw ScannerError.invalidImage
        }
        
        let request = VNDetectFaceRectanglesRequest()
        
        let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
        try handler.perform([request])
        
        return !(request.results?.isEmpty ?? true)
    }
    
    func cropDocumentFromImage(image: UIImage) async throws -> UIImage {
        guard let cgImage = image.cgImage else {
            throw ScannerError.invalidImage
        }
        
        // Use Vision to detect document rectangle
        let request = VNDetectDocumentSegmentationRequest()
        
        let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
        try handler.perform([request])
        
        guard let observation = request.results?.first else {
            return image // Return original if no document detected
        }
        
        // Get the normalized rectangle
        let rectangle = observation.topLevelResult?.normalizedBoundingBox
        
        guard let rect = rectangle else {
            return image
        }
        
        // Convert to image coordinates
        let imageSize = CGSize(width: cgImage.width, height: cgImage.height)
        let imageRect = VNImageRectForNormalizedRect(rect, Int(imageSize.width), Int(imageSize.height))
        
        // Crop the image
        guard let croppedCGImage = cgImage.cropping(to: imageRect) else {
            return image
        }
        
        return UIImage(cgImage: croppedCGImage)
    }
    
    private func extractIDNumber(from text: String) -> String? {
        // Common ID patterns for Zimbabwe
        let patterns = [
            "\\b\\d{2}[A-Z]{5}\\d{4}[A-Z]\\b", // Zimbabwe ID pattern
            "\\b\\d{13}\\b", // 13-digit ID
            "\\b[A-Z]{2}\\d{6}[A-Z]\\b" // Passport pattern
        ]
        
        for pattern in patterns {
            if let regex = try? NSRegularExpression(pattern: pattern),
               let match = regex.firstMatch(in: text, range: NSRange(text.startIndex..., in: text)),
               let range = Range(match.range, in: text) {
                return String(text[range])
            }
        }
        
        return nil
    }
    
    private func extractName(from text: String) -> String? {
        // Look for name patterns
        let lines = text.components(separatedBy: "\n")
        
        for line in lines {
            let words = line.components(separatedBy: " ").filter { !$0.isEmpty }
            if words.count >= 2 && words.count <= 4 {
                // Check if words look like names (start with capital letter)
                let allCapitals = words.allSatisfy { $0.first?.isUppercase == true }
                if allCapitals && words.allSatisfy({ $0.allSatisfy({ $0.isLetter || $0 == "-" }) }) {
                    return line
                }
            }
        }
        
        return nil
    }
    
    private func extractDateOfBirth(from text: String) -> String? {
        // Date patterns: DD/MM/YYYY, DD-MM-YYYY, YYYY-MM-DD
        let patterns = [
            "\\b\\d{2}/\\d{2}/\\d{4}\\b",
            "\\b\\d{2}-\\d{2}-\\d{4}\\b",
            "\\b\\d{4}-\\d{2}-\\d{2}\\b"
        ]
        
        for pattern in patterns {
            if let regex = try? NSRegularExpression(pattern: pattern),
               let match = regex.firstMatch(in: text, range: NSRange(text.startIndex..., in: text)),
               let range = Range(match.range, in: text) {
                let dateString = String(text[range])
                // Validate it's a reasonable birth year (1900-2006)
                if let year = Int(dateString.suffix(4)), year >= 1900 && year <= 2006 {
                    return dateString
                }
            }
        }
        
        return nil
    }
}

extension DocumentScanner: VNDocumentCameraViewControllerDelegate {
    func documentCameraViewController(_ controller: VNDocumentCameraViewController, didFinishWith scan: VNDocumentCameraScan) {
        controller.dismiss(animated: true)
        
        var images: [UIImage] = []
        for i in 0..<scan.pageCount {
            images.append(scan.imageOfPage(at: i))
        }
        
        self.scannedImages = images
        self.isScanning = false
    }
    
    func documentCameraViewControllerDidCancel(_ controller: VNDocumentCameraViewController) {
        controller.dismiss(animated: true)
        self.isScanning = false
    }
    
    func documentCameraViewController(_ controller: VNDocumentCameraViewController, didFailWithError error: Error) {
        controller.dismiss(animated: true)
        self.errorMessage = error.localizedDescription
        self.isScanning = false
    }
}

struct IDDocumentData {
    let idNumber: String?
    let fullName: String?
    let dateOfBirth: String?
    let rawText: String
    let image: UIImage
}

enum ScannerError: LocalizedError {
    case invalidImage
    case noTextFound
    case notSupported
    
    var errorDescription: String? {
        switch self {
        case .invalidImage:
            return "Invalid image provided"
        case .noTextFound:
            return "No text could be detected in the document"
        case .notSupported:
            return "Document scanning is not supported on this device"
        }
    }
}
