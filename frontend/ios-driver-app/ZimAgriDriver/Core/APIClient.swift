import Foundation
import Combine

@MainActor
class APIClient {
    static let shared = APIClient()
    
    private let baseURL: String
    private let session: URLSession
    private var authToken: String?
    
    private init() {
        self.baseURL = APIConfig.baseURL
        let configuration = URLSessionConfiguration.default
        configuration.timeoutIntervalForRequest = APIConfig.timeout
        self.session = URLSession(configuration: configuration)
        
        loadAuthToken()
    }
    
    func setAuthToken(_ token: String) {
        self.authToken = token
        KeychainManager.shared.save(token, key: "authToken")
    }
    
    func clearAuthToken() {
        self.authToken = nil
        KeychainManager.shared.delete(key: "authToken")
    }
    
    private func loadAuthToken() {
        self.authToken = KeychainManager.shared.load(key: "authToken")
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
            throw APIError.invalidResponse
        }
        
        guard 200..<300 ~= httpResponse.statusCode else {
            throw try decodeError(data: data, statusCode: httpResponse.statusCode)
        }
        
        return try JSONDecoder().decode(T.self, from: data)
    }
    
    func post<T: Decodable, U: Encodable>(_ endpoint: String, body: U) async throws -> T {
        let requestData = try JSONEncoder().encode(body)
        let request = createRequest(endpoint: endpoint, method: "POST", body: requestData)
        let (data, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }
        
        guard 200..<300 ~= httpResponse.statusCode else {
            throw try decodeError(data: data, statusCode: httpResponse.statusCode)
        }
        
        return try JSONDecoder().decode(T.self, from: data)
    }
    
    func put<T: Decodable, U: Encodable>(_ endpoint: String, body: U) async throws -> T {
        let requestData = try JSONEncoder().encode(body)
        let request = createRequest(endpoint: endpoint, method: "PUT", body: requestData)
        let (data, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }
        
        guard 200..<300 ~= httpResponse.statusCode else {
            throw try decodeError(data: data, statusCode: httpResponse.statusCode)
        }
        
        return try JSONDecoder().decode(T.self, from: data)
    }
    
    func delete<T: Decodable>(_ endpoint: String) async throws -> T {
        let request = createRequest(endpoint: endpoint, method: "DELETE")
        let (data, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }
        
        guard 200..<300 ~= httpResponse.statusCode else {
            throw try decodeError(data: data, statusCode: httpResponse.statusCode)
        }
        
        return try JSONDecoder().decode(T.self, from: data)
    }
    
    private func decodeError(data: Data, statusCode: Int) throws -> Error {
        if let errorResponse = try? JSONDecoder().decode(ErrorResponse.self, from: data) {
            return APIError.serverError(errorResponse.detail)
        }
        return APIError.unknownError(statusCode)
    }
}

enum APIError: LocalizedError {
    case invalidResponse
    case serverError(String)
    case unknownError(Int)
    
    var errorDescription: String? {
        switch self {
        case .invalidResponse:
            return "Invalid response from server"
        case .serverError(let message):
            return message
        case .unknownError(let code):
            return "Unknown error with status code: \(code)"
        }
    }
}

struct ErrorResponse: Decodable {
    let detail: String
}
