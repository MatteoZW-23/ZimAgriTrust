import SwiftUI
import Charts

struct AnalyticsView: View {
    @StateObject private var viewModel = AnalyticsViewModel()
    
    var body: some View {
        ScrollView {
            VStack(spacing: 20) {
                // Summary Cards
                HStack(spacing: 12) {
                    SummaryCard(title: "Total Sales", value: "$\(viewModel.totalSales)", icon: "dollarsign.circle", color: .green)
                    SummaryCard(title: "Listings", value: "\(viewModel.totalListings)", icon: "list.bullet", color: .blue)
                }
                
                HStack(spacing: 12) {
                    SummaryCard(title: "Completed", value: "\(viewModel.completedOrders)", icon: "checkmark.circle", color: .green)
                    SummaryCard(title: "Pending", value: "\(viewModel.pendingOrders)", icon: "clock", color: .orange)
                }
                
                // Sales Chart
                VStack(alignment: .leading, spacing: 12) {
                    Text("Sales Over Time")
                        .font(.headline)
                    
                    Chart(viewModel.salesData) { item in
                        BarMark(
                            x: .value("Date", item.date),
                            y: .value("Sales", item.amount)
                        )
                        .foregroundStyle(.blue)
                    }
                    .frame(height: 200)
                    .chartYAxis {
                        AxisMarks(position: .leading)
                    }
                }
                .padding()
                .background(Color.gray.opacity(0.1))
                .cornerRadius(12)
                
                // Crop Distribution
                VStack(alignment: .leading, spacing: 12) {
                    Text("Crop Distribution")
                        .font(.headline)
                    
                    Chart(viewModel.cropDistribution) { item in
                        SectorMark(
                            angle: .value("Quantity", item.quantity),
                            innerRadius: .ratio(0.5),
                            angularInset: 2
                        )
                        .foregroundStyle(by: .value("Crop", item.crop))
                    }
                    .frame(height: 200)
                    .chartLegend(position: .bottom, alignment: .center)
                }
                .padding()
                .background(Color.gray.opacity(0.1))
                .cornerRadius(12)
                
                // Price Trends
                VStack(alignment: .leading, spacing: 12) {
                    Text("Price Trends")
                        .font(.headline)
                    
                    Chart(viewModel.priceTrends) { item in
                        LineMark(
                            x: .value("Date", item.date),
                            y: .value("Price", item.price)
                        )
                        .foregroundStyle(.green)
                        .interpolationMethod(.catmullRom)
                    }
                    .frame(height: 200)
                    .chartYAxis {
                        AxisMarks(position: .leading)
                    }
                }
                .padding()
                .background(Color.gray.opacity(0.1))
                .cornerRadius(12)
                
                // Transaction Status
                VStack(alignment: .leading, spacing: 12) {
                    Text("Transaction Status")
                        .font(.headline)
                    
                    Chart(viewModel.transactionStatus) { item in
                        BarMark(
                            x: .value("Status", item.status),
                            y: .value("Count", item.count)
                        )
                        .foregroundStyle(by: .value("Status", item.status))
                    }
                    .frame(height: 200)
                }
                .padding()
                .background(Color.gray.opacity(0.1))
                .cornerRadius(12)
            }
            .padding()
        }
        .navigationTitle("Analytics")
        .task {
            await viewModel.loadAnalytics()
        }
    }
}

struct SummaryCard: View {
    let title: String
    let value: String
    let icon: String
    let color: Color
    
    var body: some View {
        VStack(spacing: 8) {
            Image(systemName: icon)
                .font(.title2)
                .foregroundColor(color)
            
            Text(title)
                .font(.caption)
                .foregroundColor(.secondary)
            
            Text(value)
                .font(.headline)
                .fontWeight(.bold)
        }
        .frame(maxWidth: .infinity)
        .padding()
        .background(Color.gray.opacity(0.1))
        .cornerRadius(12)
    }
}

@MainActor
class AnalyticsViewModel: ObservableObject {
    @Published var totalSales = "0"
    @Published var totalListings = 0
    @Published var completedOrders = 0
    @Published var pendingOrders = 0
    @Published var salesData: [SalesDataPoint] = []
    @Published var cropDistribution: [CropDataPoint] = []
    @Published var priceTrends: [PriceDataPoint] = []
    @Published var transactionStatus: [TransactionStatusData] = []
    
    func loadAnalytics() async {
        // In production, this would fetch from the API
        // For now, use mock data
        
        totalSales = "5,420"
        totalListings = 45
        completedOrders = 38
        pendingOrders = 7
        
        salesData = generateMockSalesData()
        cropDistribution = generateMockCropDistribution()
        priceTrends = generateMockPriceTrends()
        transactionStatus = generateMockTransactionStatus()
    }
    
    private func generateMockSalesData() -> [SalesDataPoint] {
        let calendar = Calendar.current
        let today = Date()
        
        return (0..<7).map { dayOffset in
            let date = calendar.date(byAdding: .day, value: -dayOffset, to: today) ?? today
            return SalesDataPoint(
                date: date,
                amount: Double.random(in: 500...1500)
            )
        }.reversed()
    }
    
    private func generateMockCropDistribution() -> [CropDataPoint] {
        return [
            CropDataPoint(crop: "Maize", quantity: 5000),
            CropDataPoint(crop: "Tomatoes", quantity: 3000),
            CropDataPoint(crop: "Potatoes", quantity: 2500),
            CropDataPoint(crop: "Groundnuts", quantity: 2000),
            CropDataPoint(crop: "Sugar Beans", quantity: 1500)
        ]
    }
    
    private func generateMockPriceTrends() -> [PriceDataPoint] {
        let calendar = Calendar.current
        let today = Date()
        
        return (0..<30).map { dayOffset in
            let date = calendar.date(byAdding: .day, value: -dayOffset, to: today) ?? today
            return PriceDataPoint(
                date: date,
                price: 0.50 + Double.random(in: -0.10...0.10)
            )
        }.reversed()
    }
    
    private func generateMockTransactionStatus() -> [TransactionStatusData] {
        return [
            TransactionStatusData(status: "Completed", count: 38),
            TransactionStatusData(status: "Pending", count: 7),
            TransactionStatusData(status: "Cancelled", count: 3)
        ]
    }
}

struct SalesDataPoint: Identifiable {
    let id = UUID()
    let date: Date
    let amount: Double
}

struct CropDataPoint: Identifiable {
    let id = UUID()
    let crop: String
    let quantity: Double
}

struct PriceDataPoint: Identifiable {
    let id = UUID()
    let date: Date
    let price: Double
}

struct TransactionStatusData: Identifiable {
    let id = UUID()
    let status: String
    let count: Int
}

#Preview {
    AnalyticsView()
}
