import Foundation
import Combine

@MainActor
class SharedAPIClient {
    static let shared = SharedAPIClient()
    
    private let baseURL: String
    private let session: URLSession
    private var authToken: String?
    
    private init() {
        self.baseURL = APIConfig.shared.baseURL
        let configuration = URLSessionConfiguration.default
        configuration.timeoutIntervalForRequest = 30.0
        self.session = URLSession(configuration: configuration)
    }
    
    func setAuthToken(_ token: String) {
        self.authToken = token
    }
    
    func clearAuthToken() {
        self.authToken = nil
    }
    
    private func createRequest(endpoint: String, method: String = "GET", body: Data? = nil) -> URLRequest {
        guard let url = URL(string: baseURL + endpoint) else {
            fatalError("Invalid URL: \(baseURL)\(endpoint)")
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        
        if let token = authToken {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        
        if let body = body {
            request.httpBody = body
        }
        
        return request
    }
    
    func get<T: Decodable>(_ endpoint: String) async throws -> T {
        let request = createRequest(endpoint: endpoint, method: "GET")
        let (data, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.networkError
        }
        
        guard 200..<300 ~= httpResponse.statusCode else {
            throw APIError.serverError("HTTP \(httpResponse.statusCode)")
        }
        
        return try JSONDecoder().decode(T.self, from: data)
    }
    
    func post<T: Decodable, U: Encodable>(_ endpoint: String, body: U) async throws -> T {
        let requestData = try JSONEncoder().encode(body)
        let request = createRequest(endpoint: endpoint, method: "POST", body: requestData)
        let (data, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.networkError
        }
        
        guard 200..<300 ~= httpResponse.statusCode else {
            throw APIError.serverError("HTTP \(httpResponse.statusCode)")
        }
        
        return try JSONDecoder().decode(T.self, from: data)
    }
    
    func put<T: Decodable, U: Encodable>(_ endpoint: String, body: U) async throws -> T {
        let requestData = try JSONEncoder().encode(body)
        let request = createRequest(endpoint: endpoint, method: "PUT", body: requestData)
        let (data, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.networkError
        }
        
        guard 200..<300 ~= httpResponse.statusCode else {
            throw APIError.serverError("HTTP \(httpResponse.statusCode)")
        }
        
        return try JSONDecoder().decode(T.self, from: data)
    }
    
    func delete<T: Decodable>(_ endpoint: String) async throws -> T {
        let request = createRequest(endpoint: endpoint, method: "DELETE")
        let (data, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.networkError
        }
        
        guard 200..<300 ~= httpResponse.statusCode else {
            throw APIError.serverError("HTTP \(httpResponse.statusCode)")
        }
        
        return try JSONDecoder().decode(T.self, from: data)
    }
}

class APIConfig {
    static let shared = APIConfig()
    
    var baseURL: String {
        #if DEBUG
        return "http://localhost:8080/api/v1"
        #else
        return "https://api.zimagritrust.com/api/v1"
        #endif
    }
    
    private init() {}
}
