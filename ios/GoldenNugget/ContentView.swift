//
//  ContentView.swift
//  GoldenNugget
//

import SwiftUI

private enum Constants {
    static let disabledPlistPath = "/var/db/com.apple.xpc.launchd/disabled.plist"
}

struct ContentView: View {
    @StateObject private var store = StateStore()
    @State private var searchText = ""
    @State private var appliedMessage: String?

    var body: some View {
        NavigationStack {
            List {
                masterSection
                selectAllSection
                adlSection
                otherSection
            }
            .searchable(text: $searchText, prompt: "Search daemons")
            .navigationTitle("GoldenNugget (iOS)")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button("Apply") {
                        applyChanges()
                    }
                    .disabled(!store.masterEnabled)
                }
            }
            .task {
                loadExistingDisabled()
            }
            .alert("Apply Daemons", isPresented: Binding(
                get: { appliedMessage != nil },
                set: { if !$0 { appliedMessage = nil } }
            )) {
                Button("OK", role: .cancel) { appliedMessage = nil }
            } message: {
                Text(appliedMessage ?? "")
            }
        }
    }

    private var masterSection: some View {
        Section {
            Toggle(isOn: $store.masterEnabled) {
                Text("Enable Daemon Modifications")
                    .font(.body)
            }
        }
    }

    private var selectAllSection: some View {
        Section {
            Toggle(isOn: Binding(
                get: { store.recommendedAllOn() },
                set: { on in store.setEnabled(store.recommendedDaemons(), on) }
            )) {
                Text("Recommended (analytics, tracking & logging)")
                    .fontWeight(.semibold)
            }
        } footer: {
            Text("Enable the recommended set of telemetry, analytics, and tracking daemons at once.")
        }
    }

    private var adlSection: some View {
        let adl = filteredDaemons(in: [.LOGGING, .ANALYTICS, .TRACKING])
        if adl.isEmpty {
            return AnyView(EmptyView())
        }
        return AnyView(Section("Analytics, Data Tracking & Logging") {
            ForEach(adl) { daemon in
                daemonRow(daemon)
            }
        })
    }

    private var otherSection: some View {
        let other = filteredDaemons(in: [.OTHER])
        if other.isEmpty {
            return AnyView(EmptyView())
        }
        return AnyView(Section("Other") {
            ForEach(other) { daemon in
                daemonRow(daemon)
            }
        })
    }

    private func filteredDaemons(in cats: [DaemonCategory]) -> [DaemonDef] {
        let catNames = Set(cats.map { $0.rawValue })
        let matches = store.catalog.daemons.filter { catNames.contains($0.category) }
        if searchText.isEmpty {
            return matches
        }
        return matches.filter {
            $0.name.localizedCaseInsensitiveContains(searchText) ||
            $0.title.localizedCaseInsensitiveContains(searchText) ||
            $0.description.localizedCaseInsensitiveContains(searchText)
        }
    }

    @ViewBuilder
    private func daemonRow(_ daemon: DaemonDef) -> some View {
        Toggle(isOn: Binding(
            get: { store.isOn(daemon) },
            set: { on in store.setEnabled(daemon, on) }
        )) {
            VStack(alignment: .leading, spacing: 2) {
                Text(daemon.title)
                if !daemon.description.isEmpty {
                    Text(daemon.description)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
        }
    }

    func loadExistingDisabled() {
        guard let handle = consumeExtension(Constants.disabledPlistPath) else {
            return
        }
        defer { bad_query_release(handle) }

        let url = URL(fileURLWithPath: Constants.disabledPlistPath)
        guard let data = try? Data(contentsOf: url),
              let plist = (try? PropertyListSerialization.propertyList(from: data,
                                                                       options: [],
                                                                       format: nil)) as? [String: Any]
        else {
            return
        }
        let existing = plist.compactMap { key, value -> String? in
            guard key.hasPrefix("com.apple."), let flag = value as? Bool, flag else { return nil }
            return key
        }
        DispatchQueue.main.async {
            store.enabledLabels = Set(existing)
            store.masterEnabled = !existing.isEmpty
        }
    }

    func applyChanges() {
        let labels = store.enabledLabels.sorted()
        let plistDict: [String: Bool] = Dictionary(uniqueKeysWithValues: labels.map { ($0, true) })

        guard let handle = consumeExtension(Constants.disabledPlistPath) else {
            store.lastError = "bad_query failed to grant access to \(Constants.disabledPlistPath)"
            appliedMessage = store.lastError
            return
        }
        defer { bad_query_release(handle) }

        do {
            let data = try PropertyListSerialization.data(fromPropertyList: plistDict,
                                                          format: .xml,
                                                          options: 0)
            try data.write(to: URL(fileURLWithPath: Constants.disabledPlistPath))
            appliedMessage = "Wrote \(labels.count) disabled daemons. Restart device to apply."
        } catch {
            store.lastError = error.localizedDescription
            appliedMessage = store.lastError
        }
    }

    private func consumeExtension(_ path: String) -> Int64? {
        var pathC = path.utf8CString.map { Int8($0) }
        let handle = bad_query(&pathC, false, nil, false)
        if handle < 0 {
            print("bad_query failed with handle \(handle)")
            return nil
        }
        return handle
    }
}

#Preview {
    ContentView()
}