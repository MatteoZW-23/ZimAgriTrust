import Foundation
import PencilKit
import UIKit

@MainActor
class SignatureManager: ObservableObject {
    @Published var signatureImage: UIImage?
    @Published var hasSignature = false
    @Published var signatureData: Data?
    
    private let drawing = PKDrawing()
    private var tool: PKTool = PKInkingTool(.pen, color: .black, width: 5)
    
    func clearSignature() {
        signatureImage = nil
        hasSignature = false
        signatureData = nil
    }
    
    func saveSignature(from drawing: PKDrawing, in rect: CGRect) {
        let image = drawing.image(from: rect, scale: UIScreen.main.scale)
        self.signatureImage = image
        self.hasSignature = true
        
        if let data = image.pngData() {
            self.signatureData = data
        }
    }
    
    func getSignatureAsBase64() -> String? {
        guard let data = signatureData else { return nil }
        return data.base64EncodedString()
    }
    
    func validateSignature() -> Bool {
        guard hasSignature, let image = signatureImage else { return false }
        
        // Check if signature has sufficient content
        let size = image.size
        let minSize: CGFloat = 50
        
        guard size.width >= minSize && size.height >= minSize else { return false }
        
        // Check if image is not blank (has non-transparent pixels)
        guard let cgImage = image.cgImage else { return false }
        
        let width = cgImage.width
        let height = cgImage.height
        let bytesPerRow = cgImage.bytesPerRow
        let bitsPerComponent = cgImage.bitsPerComponent
        
        guard let pixelData = cgImage.dataProvider?.data else { return false }
        let data = CFDataGetBytePtr(pixelData)
        
        var nonTransparentPixels = 0
        for y in 0..<height {
            for x in 0..<width {
                let pixelIndex = (y * bytesPerRow) + (x * 4)
                let alpha = data[pixelIndex + 3]
                if alpha > 0 {
                    nonTransparentPixels += 1
                }
            }
        }
        
        let totalPixels = width * height
        let filledRatio = Double(nonTransparentPixels) / Double(totalPixels)
        
        // Signature should have at least 1% filled pixels but not more than 50%
        return filledRatio >= 0.01 && filledRatio <= 0.5
    }
    
    func createSignatureView() -> SignatureCanvasView {
        return SignatureCanvasView(signatureManager: self)
    }
}

class SignatureCanvasView: UIView {
    private let canvasView: PKCanvasView
    private let toolPicker: PKToolPicker
    private weak var signatureManager: SignatureManager?
    
    init(signatureManager: SignatureManager) {
        self.signatureManager = signatureManager
        self.canvasView = PKCanvasView()
        self.toolPicker = PKToolPicker()
        
        super.init(frame: .zero)
        
        setupCanvas()
        setupToolPicker()
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
    
    private func setupCanvas() {
        canvasView.drawingPolicy = .anyInput
        canvasView.backgroundColor = .white
        canvasView.layer.borderWidth = 1
        canvasView.layer.borderColor = UIColor.systemGray4.cgColor
        canvasView.layer.cornerRadius = 8
        
        canvasView.translatesAutoresizingMaskIntoConstraints = false
        addSubview(canvasView)
        
        NSLayoutConstraint.activate([
            canvasView.topAnchor.constraint(equalTo: topAnchor),
            canvasView.leadingAnchor.constraint(equalTo: leadingAnchor),
            canvasView.trailingAnchor.constraint(equalTo: trailingAnchor),
            canvasView.bottomAnchor.constraint(equalTo: bottomAnchor)
        ])
    }
    
    private func setupToolPicker() {
        toolPicker.addObserver(canvasView)
        toolPicker.setVisible(true, forFirstResponder: canvasView)
        canvasView.becomeFirstResponder()
    }
    
    func saveSignature() {
        let rect = canvasView.bounds
        signatureManager?.saveSignature(from: canvasView.drawing, in: rect)
    }
    
    func clearSignature() {
        canvasView.drawing = PKDrawing()
        signatureManager?.clearSignature()
    }
    
    override func didMoveToWindow() {
        super.didMoveToWindow()
        
        guard let window = window else { return }
        toolPicker.setVisible(true, forFirstResponder: canvasView)
        toolPicker.addObserver(canvasView)
    }
}
