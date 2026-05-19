//
//  MarketTabView.swift
//  ZimAgriTrust
//
//  Market tab with prices, trends, and news
//

import SwiftUI

struct MarketTabView: View {
    @StateObject private var marketService = MarketService.shared
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 20) {
                    // Market Summary Card
                    if let summary = marketService.summary {
                        MarketSummaryCard(summary: summary)
                    }
                    
                    // Market Prices
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Current Prices")
                            .font(.headline)
                            .padding(.horizontal)
                        
                        ScrollView(.horizontal, showsIndicators: false) {
                            HStack(spacing: 12) {
                                ForEach(marketService.prices) { price in
                                    PriceCard(price: price)
                                }
                            }
                            .padding(.horizontal)
                        }
                    }
                    
                    // Trending Crops
                    if !marketService.trendingCrops.isEmpty {
                        VStack(alignment: .leading, spacing: 12) {
                            Text("Trending Crops")
                                .font(.headline)
                                .padding(.horizontal)
                            
                            VStack(spacing: 8) {
                                ForEach(marketService.trendingCrops) { crop in
                                    TrendingCropRow(crop: crop)
                                }
                            }
                            .padding(.horizontal)
                        }
                    }
                    
                    // Market News
                    if !marketService.news.isEmpty {
                        VStack(alignment: .leading, spacing: 12) {
                            Text("Market News")
                                .font(.headline)
                                .padding(.horizontal)
                            
                            VStack(spacing: 8) {
                                ForEach(marketService.news) { news in
                                    NewsCard(news: news)
                                }
                            }
                            .padding(.horizontal)
                        }
                    }
                }
                .padding(.vertical)
            }
            .navigationTitle("Market")
            .refreshable {
                await refreshMarketData()
            }
            .onAppear {
                Task {
                    await refreshMarketData()
                }
            }
        }
    }
    
    private func refreshMarketData() async {
        async let prices = marketService.fetchMarketPrices()
        async let trending = marketService.fetchTrendingCrops()
        async let news = marketService.fetchMarketNews()
        async let summary = marketService.fetchMarketSummary()
        
        try? await prices
        try? await trending
        try? await news
        try? await summary
    }
}

struct MarketSummaryCard: View {
    let summary: MarketSummary
    
    var body: some View {
        VStack(spacing: 12) {
            HStack {
                Label("Market Summary", systemImage: "chart.bar.fill")
                    .font(.headline)
                Spacer()
            }
            
            HStack(spacing: 20) {
                StatItem(title: "Listings", value: "\(summary.total_listings)")
                StatItem(title: "Transactions", value: "\(summary.active_transactions)")
                StatItem(title: "Volume", value: "\(Int(summary.total_volume_kg)) kg")
            }
            
            if !summary.top_crops.isEmpty {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Top Crops")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    
                    Text(summary.top_crops.prefix(3).joined(separator: ", "))
                        .font(.subheadline)
                }
            }
        }
        .padding()
        .background(Color(UIColor.systemGray6))
        .cornerRadius(12)
        .padding(.horizontal)
    }
}

struct StatItem: View {
    let title: String
    let value: String
    
    var body: some View {
        VStack(spacing: 4) {
            Text(value)
                .font(.title3)
                .fontWeight(.bold)
            
            Text(title)
                .font(.caption)
                .foregroundColor(.secondary)
        }
    }
}

struct PriceCard: View {
    let price: MarketPrice
    
    var body: some View {
        VStack(spacing: 8) {
            Text(price.crop_type.capitalized)
                .font(.headline)
            
            Text(price.formattedPrice)
                .font(.title2)
                .fontWeight(.bold)
                .foregroundColor(.green)
            
            Text(price.changeIndicator)
                .font(.caption)
                .foregroundColor(price.changePercent ?? 0 >= 0 ? .green : .red)
        }
        .frame(width: 120)
        .padding()
        .background(Color(UIColor.systemGray6))
        .cornerRadius(12)
    }
}

struct TrendingCropRow: View {
    let crop: TrendingCrop
    
    var body: some View {
        HStack {
            Text(crop.crop_type.capitalized)
                .font(.subheadline)
                .frame(maxWidth: .infinity, alignment: .leading)
            
            Text("Demand: \(Int(crop.demand_score))")
                .font(.caption)
                .foregroundColor(.secondary)
            
            Text(crop.price_trend)
                .font(.caption)
                .fontWeight(.semibold)
                .foregroundColor(crop.price_trend.contains("up") ? .green : .red)
        }
        .padding()
        .background(Color(UIColor.systemGray6))
        .cornerRadius(8)
    }
}

struct NewsCard: View {
    let news: MarketNews
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(news.title)
                .font(.subheadline)
                .fontWeight(.semibold)
            
            if let summary = news.summary {
                Text(summary)
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .lineLimit(2)
            }
            
            HStack {
                Text(news.source ?? "Unknown")
                    .font(.caption2)
                    .foregroundColor(.secondary)
                
                Spacer()
                
                Text(formatDate(news.published_at))
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }
        }
        .padding()
        .background(Color(UIColor.systemGray6))
        .cornerRadius(8)
    }
    
    private func formatDate(_ dateString: String) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "ISO8601"
        
        guard let date = formatter.date(from: dateString) else {
            return dateString
        }
        
        formatter.dateStyle = .short
        return formatter.string(from: date)
    }
}

#Preview {
    MarketTabView()
}
