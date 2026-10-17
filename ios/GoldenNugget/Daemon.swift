//
//  Daemon.swift
//  GoldenNugget
//

import Foundation

struct DaemonDef: Codable, Identifiable, Hashable {
    var id: String { name }
    let name: String
    let labels: [String]
    let category: String
    let title: String
    let description: String
}

enum DaemonCategory: String, Codable, CaseIterable {
    case LOGGING
    case ANALYTICS
    case TRACKING
    case OTHER

    var displayName: String {
        switch self {
        case .LOGGING: return "Logging"
        case .ANALYTICS: return "Analytics"
        case .TRACKING: return "Data Tracking"
        case .OTHER: return "Other"
        }
    }
}

struct DaemonCatalog: Codable {
    let generatedFrom: String
    let recommended: [String]
    let daemons: [DaemonDef]

    enum CodingKeys: String, CodingKey {
        case generatedFrom = "generated_from"
        case recommended
        case daemons
    }
}

enum CatalogLoader {
    static func load() -> DaemonCatalog {
        guard let url = Bundle.main.url(forResource: "daemons", withExtension: "json"),
              let data = try? Data(contentsOf: url),
              let catalog = try? JSONDecoder().decode(DaemonCatalog.self, from: data)
        else {
            print("Failed to load daemons.json")
            return DaemonCatalog(generatedFrom: "", recommended: [], daemons: [])
        }
        return catalog
    }
}

final class StateStore: ObservableObject {
    @Published var enabledLabels: Set<String> = []
    @Published var masterEnabled: Bool = false
    @Published var lastError: String?

    let catalog = CatalogLoader.load()

    func isOn(_ daemon: DaemonDef) -> Bool {
        return daemon.labels.contains { enabledLabels.contains($0) }
    }

    func setEnabled(_ daemon: DaemonDef, _ on: Bool) {
        if on {
            enabledLabels.formUnion(daemon.labels)
        } else {
            enabledLabels.subtract(daemon.labels)
        }
        if on {
            masterEnabled = true
        }
    }

    func setEnabled(_ daemons: [DaemonDef], _ on: Bool) {
        for daemon in daemons {
            if on {
                enabledLabels.formUnion(daemon.labels)
            } else {
                enabledLabels.subtract(daemon.labels)
            }
        }
        if on {
            masterEnabled = true
        }
    }

    func recommendedDaemons() -> [DaemonDef] {
        let names = Set(catalog.recommended)
        return catalog.daemons.filter { names.contains($0.name) }
    }

    func recommendedAllOn() -> Bool {
        let rec = recommendedDaemons()
        guard !rec.isEmpty else { return false }
        return rec.allSatisfy { isOn($0) }
    }
}