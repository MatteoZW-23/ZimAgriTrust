import Foundation
import CarPlay

@available(iOS 14.0, *)
class CarPlaySceneDelegate: NSObject, CPTemplateApplicationSceneDelegate {
    var interfaceController: CPInterfaceController?
    
    func templateApplicationScene(_ templateApplicationScene: CPTemplateApplicationScene, didConnect interfaceController: CPInterfaceController) {
        self.interfaceController = interfaceController
        
        // Set up the main CarPlay template
        let mainTemplate = createMainTemplate()
        interfaceController.setRootTemplate(mainTemplate, animated: true)
    }
    
    func templateApplicationScene(_ templateApplicationScene: CPTemplateApplicationScene, didDisconnect interfaceController: CPInterfaceController) {
        self.interfaceController = nil
    }
    
    private func createMainTemplate() -> CPTemplate {
        // Create a list template with main actions
        let activeDeliveriesItem = CPListItem(text: "Active Deliveries", detailText: "View current deliveries")
        activeDeliveriesItem.handler = { [weak self] item, completion in
            self?.showActiveDeliveries()
            completion(true)
        }
        
        let navigationItem = CPListItem(text: "Navigation", detailText: "Start navigation to destination")
        navigationItem.handler = { [weak self] item, completion in
            self?.showNavigation()
            completion(true)
        }
        
        let profileItem = CPListItem(text: "Driver Profile", detailText: "View your profile")
        profileItem.handler = { [weak self] item, completion in
            self?.showProfile()
            completion(true)
        }
        
        let listTemplate = CPListTemplate(title: "ZimAgriDriver", sections: [
            CPListSection(items: [activeDeliveriesItem, navigationItem, profileItem], header: "Main Menu")
        ])
        
        return listTemplate
    }
    
    private func showActiveDeliveries() {
        guard let interfaceController = interfaceController else { return }
        
        // Create delivery items
        let delivery1 = CPListItem(text: "Maize - 500kg", detailText: "Harare to Bulawayo")
        delivery1.handler = { [weak self] item, completion in
            self?.showDeliveryDetails()
            completion(true)
        }
        
        let delivery2 = CPListItem(text: "Tomatoes - 200kg", detailText: "Mutare to Gweru")
        delivery2.handler = { [weak self] item, completion in
            self?.showDeliveryDetails()
            completion(true)
        }
        
        let listTemplate = CPListTemplate(title: "Active Deliveries", sections: [
            CPListSection(items: [delivery1, delivery2], header: "Today's Deliveries")
        ])
        
        interfaceController.pushTemplate(listTemplate, animated: true)
    }
    
    private func showDeliveryDetails() {
        guard let interfaceController = interfaceController else { return }
        
        let confirmPickup = CPButton(title: "Confirm Pickup", style: .normal) { [weak self] button in
            self?.confirmPickup()
        }
        
        let confirmDelivery = CPButton(title: "Confirm Delivery", style: .normal) { [weak self] button in
            self?.confirmDelivery()
        }
        
        let infoTemplate = CPInformationTemplate(title: "Delivery Details", layout: .leading, items: [
            CPInformationItem(title: "Crop", detail: "Maize"),
            CPInformationItem(title: "Quantity", detail: "500 kg"),
            CPInformationItem(title: "Pickup", detail: "Harare"),
            CPInformationItem(title: "Delivery", detail: "Bulawayo"),
            CPInformationItem(title: "Status", detail: "In Transit")
        ], actions: [confirmPickup, confirmDelivery])
        
        interfaceController.pushTemplate(infoTemplate, animated: true)
    }
    
    private func showNavigation() {
        guard let interfaceController = interfaceController else { return }
        
        // Create a navigation template
        let navigationTemplate = CPNavigationTemplate(navigationButtons: [
            CPNavigationButton(title: "Start Navigation", style: .confirm) { button in
                // Start navigation
            },
            CPNavigationButton(title: "Cancel", style: .cancel) { button in
                interfaceController.popTemplate(animated: true)
            }
        ])
        
        interfaceController.pushTemplate(navigationTemplate, animated: true)
    }
    
    private func showProfile() {
        guard let interfaceController = interfaceController else { return }
        
        let infoTemplate = CPInformationTemplate(title: "Driver Profile", layout: .leading, items: [
            CPInformationItem(title: "Name", detail: "John Doe"),
            CPInformationItem(title: "Phone", detail: "+263 123 456 789"),
            CPInformationItem(title: "Rating", detail: "4.8"),
            CPInformationItem(title: "Completed Deliveries", detail: "156")
        ])
        
        interfaceController.pushTemplate(infoTemplate, animated: true)
    }
    
    private func confirmPickup() {
        // Call backend to confirm pickup
        NotificationCenter.default.post(name: .confirmPickup, object: nil)
    }
    
    private func confirmDelivery() {
        // Call backend to confirm delivery
        NotificationCenter.default.post(name: .confirmDelivery, object: nil)
    }
}

extension Notification.Name {
    static let confirmPickup = Notification.Name("carPlayConfirmPickup")
    static let confirmDelivery = Notification.Name("carPlayConfirmDelivery")
}
