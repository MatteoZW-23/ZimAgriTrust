//
//  CoreDataStack.swift
//  ZimAgriTrust
//
//  CoreData stack for offline storage
//

import Foundation
import CoreData
import Combine

class CoreDataStack {
    static let shared = CoreDataStack()
    
    lazy var persistentContainer: NSPersistentContainer = {
        let container = NSPersistentContainer(name: "ZimAgriTrust")
        container.loadPersistentStores { description, error in
            if let error = error {
                fatalError("Core Data store failed to load: \(error)")
            }
        }
        container.viewContext.automaticallyMergesChangesFromParent = true
        return container
    }()
    
    var viewContext: NSManagedObjectContext {
        return persistentContainer.viewContext
    }
    
    var backgroundContext: NSManagedObjectContext {
        let context = persistentContainer.newBackgroundContext()
        context.mergePolicy = NSMergeByPropertyObjectTrumpMergePolicy
        return context
    }
    
    func save() {
        let context = viewContext
        
        if context.hasChanges {
            do {
                try context.save()
            } catch {
                print("Core Data save error: \(error)")
            }
        }
    }
    
    func saveBackground() {
        let context = backgroundContext
        
        context.perform {
            if context.hasChanges {
                do {
                    try context.save()
                } catch {
                    print("Core Data background save error: \(error)")
                }
            }
        }
    }
}

// MARK: - Generic CRUD Operations

extension CoreDataStack {
    func fetch<T: NSManagedObject>(
        _ type: T.Type,
        predicate: NSPredicate? = nil,
        sortDescriptors: [NSSortDescriptor]? = nil
    ) -> [T] {
        let request = NSFetchRequest<T>(entityName: String(describing: type))
        request.predicate = predicate
        request.sortDescriptors = sortDescriptors
        
        do {
            return try viewContext.fetch(request)
        } catch {
            print("Core Data fetch error: \(error)")
            return []
        }
    }
    
    func create<T: NSManagedObject>(_ type: T.Type) -> T {
        let entity = NSEntityDescription.entity(forEntityName: String(describing: type), in: viewContext)!
        return T(entity: entity, insertInto: viewContext)
    }
    
    func delete<T: NSManagedObject>(_ object: T) {
        viewContext.delete(object)
        save()
    }
    
    func deleteAll<T: NSManagedObject>(_ type: T.Type) {
        let fetchRequest = NSFetchRequest<NSFetchRequestResult>(entityName: String(describing: type))
        let deleteRequest = NSBatchDeleteRequest(fetchRequest: fetchRequest)
        
        do {
            try viewContext.execute(deleteRequest)
            save()
        } catch {
            print("Core Data delete all error: \(error)")
        }
    }
}
