import WidgetKit
import SwiftUI
import Intents

struct MarketSnapshotEntry: TimelineEntry {
    let date: Date
    let marketPrices: [MarketPrice]
    let trendingCrops: [String]
    let lastUpdated: Date
}

struct MarketPrice: Identifiable {
    let id = UUID()
    let cropName: String
    let price: Double
    let change: Double
    let currency: String
}

struct MarketSnapshotProvider: TimelineProvider {
    func placeholder(in context: Context) -> MarketSnapshotEntry {
        MarketSnapshotEntry(
            date: Date(),
            marketPrices: [
                MarketPrice(cropName: "Maize", price: 0.50, change: 0.05, currency: "USD"),
                MarketPrice(cropName: "Tomatoes", price: 1.20, change: -0.10, currency: "USD"),
                MarketPrice(cropName: "Potatoes", price: 0.80, change: 0.02, currency: "USD")
            ],
            trendingCrops: ["Maize", "Tomatoes", "Groundnuts"],
            lastUpdated: Date()
        )
    }

    func getSnapshot(in context: Context, completion: @escaping (MarketSnapshotEntry) -> Void) {
        let entry = placeholder(in: context)
        completion(entry)
    }

    func getTimeline(in context: Context, completion: @escaping (Timeline<MarketSnapshotEntry>) -> Void) {
        Task {
            let marketPrices = await fetchMarketPrices()
            let trendingCrops = await fetchTrendingCrops()
            
            let entry = MarketSnapshotEntry(
                date: Date(),
                marketPrices: marketPrices,
                trendingCrops: trendingCrops,
                lastUpdated: Date()
            )
            
            let nextUpdate = Calendar.current.date(byAdding: .hour, value: 1, to: Date()) ?? Date()
            let timeline = Timeline(entries: [entry], policy: .after(nextUpdate))
            
            completion(timeline)
        }
    }
    
    private func fetchMarketPrices() async -> [MarketPrice] {
        // In production, this would call the actual API
        // For now, return mock data
        return [
            MarketPrice(cropName: "Maize", price: 0.50, change: 0.05, currency: "USD"),
            MarketPrice(cropName: "Tomatoes", price: 1.20, change: -0.10, currency: "USD"),
            MarketPrice(cropName: "Potatoes", price: 0.80, change: 0.02, currency: "USD"),
            MarketPrice(cropName: "Groundnuts", price: 1.50, change: 0.08, currency: "USD"),
            MarketPrice(cropName: "Sugar Beans", price: 1.10, change: -0.05, currency: "USD")
        ]
    }
    
    private func fetchTrendingCrops() async -> [String] {
        // In production, this would call the actual API
        return ["Maize", "Tomatoes", "Groundnuts"]
    }
}

struct MarketSnapshotWidgetEntryView: View {
    var entry: MarketSnapshotProvider.Entry
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: "chart.line.uptrend.xyaxis")
                    .foregroundColor(.green)
                Text("Market Snapshot")
                    .font(.headline)
                Spacer()
                Text("ZimAgriTrust")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            Divider()
            
            ForEach(entry.marketPrices.prefix(3)) { price in
                HStack {
                    Text(price.cropName)
                        .font(.subheadline)
                        .frame(width: 80, alignment: .leading)
                    
                    Spacer()
                    
                    Text(String(format: "$%.2f", price.price))
                        .font(.subheadline)
                        .fontWeight(.semibold)
                    
                    if price.change > 0 {
                        Image(systemName: "arrow.up.right")
                            .font(.caption)
                            .foregroundColor(.green)
                    } else if price.change < 0 {
                        Image(systemName: "arrow.down.right")
                            .font(.caption)
                            .foregroundColor(.red)
                    }
                }
            }
            
            Divider()
            
            HStack {
                Text("Trending:")
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                ForEach(entry.trendingCrops.prefix(2), id: \.self) { crop in
                    Text(crop)
                        .font(.caption)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(Color.blue.opacity(0.1))
                        .cornerRadius(4)
                }
            }
            
            Text("Updated: \(formatDate(entry.lastUpdated))")
                .font(.caption2)
                .foregroundColor(.secondary)
        }
        .padding()
    }
    
    private func formatDate(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.timeStyle = .short
        return formatter.string(from: date)
    }
}

struct MarketSnapshotWidget: Widget {
    let kind: String = "MarketSnapshotWidget"

    var body: some WidgetConfiguration {
        StaticConfiguration(kind: kind, provider: MarketSnapshotProvider()) { entry in
            MarketSnapshotWidgetEntryView(entry: entry)
                .containerBackground(.fill.tertiary, for: .widget)
        }
        .configurationDisplayName("Market Snapshot")
        .description("View current crop prices and trends")
        .supportedFamilies([.systemSmall, .systemMedium])
    }
}

@main
struct MarketSnapshotWidgetBundle: WidgetBundle {
    var body: some Widget {
        MarketSnapshotWidget()
    }
}
