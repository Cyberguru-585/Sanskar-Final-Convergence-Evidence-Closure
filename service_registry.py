

import json
import time
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import threading
import uuid


@dataclass
class ServiceEndpoint:
    
    service_id: str
    hostname: str
    port: int
    protocol: str = "http"
    
    def get_url(self) -> str:
        return f"{self.protocol}://{self.hostname}:{self.port}"


@dataclass
class ServiceCapability:
    
    capability: str
    version: str
    status: str = "READY"  


@dataclass
class ServiceRegistration:
    
    service_id: str
    service_name: str
    startup_time: str
    endpoint: Dict[str, Any]
    capabilities: List[Dict[str, Any]]
    health_status: Dict[str, Any]
    readiness: bool
    liveness: bool
    registration_timestamp: str


class ServiceRegistry:
   
    
    def __init__(self):
        self.registry: Dict[str, ServiceRegistration] = {}
        self.lock = threading.Lock()
        self.last_updated = datetime.now(timezone.utc).isoformat()
        
    def register_service(self, registration: ServiceRegistration) -> bool:
        
        with self.lock:
            self.registry[registration.service_id] = registration
            self.last_updated = datetime.now(timezone.utc).isoformat()
            return True
            
    def deregister_service(self, service_id: str) -> bool:
        
        with self.lock:
            if service_id in self.registry:
                del self.registry[service_id]
                self.last_updated = datetime.now(timezone.utc).isoformat()
                return True
            return False
            
    def get_service(self, service_id: str) -> Optional[ServiceRegistration]:
        
        with self.lock:
            return self.registry.get(service_id)
            
    def get_all_services(self) -> List[ServiceRegistration]:
        
        with self.lock:
            return list(self.registry.values())
            
    def get_services_by_name(self, service_name: str) -> List[ServiceRegistration]:
        
        with self.lock:
            return [s for s in self.registry.values() if s.service_name == service_name]
            
    def get_healthy_services(self) -> List[ServiceRegistration]:
        
        with self.lock:
            return [s for s in self.registry.values() 
                   if s.readiness and s.liveness]
                   
    def get_registry_status(self) -> Dict[str, Any]:
        
        with self.lock:
            services = list(self.registry.values())
            healthy_count = sum(1 for s in services if s.readiness and s.liveness)
            
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "total_registered": len(services),
                "healthy_services": healthy_count,
                "services": [
                    {
                        "service_id": s.service_id,
                        "service_name": s.service_name,
                        "endpoint": s.endpoint,
                        "readiness": s.readiness,
                        "liveness": s.liveness
                    }
                    for s in services
                ]
            }



_registry_instance: Optional[ServiceRegistry] = None


def get_registry() -> ServiceRegistry:
    
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = ServiceRegistry()
    return _registry_instance


class ServiceDiscoveryClient:
    
    
    def __init__(self):
        self.registry = get_registry()
        
    def discover_service(self, service_name: str) -> Optional[ServiceRegistration]:
        
        services = self.registry.get_services_by_name(service_name)
        return services[0] if services else None
        
    def discover_healthy_service(self, service_name: str) -> Optional[ServiceRegistration]:
        
        services = self.registry.get_services_by_name(service_name)
        healthy = [s for s in services if s.readiness and s.liveness]
        return healthy[0] if healthy else None
        
    def get_all_services(self) -> Dict[str, Any]:
        
        all_services = self.registry.get_all_services()
        organized = {}
        for service in all_services:
            if service.service_name not in organized:
                organized[service.service_name] = []
            organized[service.service_name].append(service)
        return organized
        
    def get_participant_network_map(self) -> Dict[str, Any]:
        
        services = self.registry.get_all_services()
        
        network_map = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_participants": len(services),
            "network_topology": {}
        }
        
        for service in services:
            network_map["network_topology"][service.service_id] = {
                "name": service.service_name,
                "endpoint": service.endpoint,
                "capabilities": service.capabilities,
                "status": "HEALTHY" if (service.readiness and service.liveness) else "UNHEALTHY"
            }
            
        return network_map


class ParticipantHealthMonitor:
    
    
    def __init__(self):
        self.registry = get_registry()
        self.health_history: Dict[str, List[Dict[str, Any]]] = {}
        
    def record_health_check(self, service_id: str, health_status: Dict[str, Any]):
        
        if service_id not in self.health_history:
            self.health_history[service_id] = []
            
        self.health_history[service_id].append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": health_status
        })
        
    def get_health_matrix(self) -> Dict[str, Any]:
       
        services = self.registry.get_all_services()
        
        matrix = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "report_type": "participant_health_matrix",
            "total_participants": len(services),
            "participants": {}
        }
        
        for service in services:
            history = self.health_history.get(service.service_id, [])
            recent_checks = history[-10:] if history else []  # Last 10 checks
            
            matrix["participants"][service.service_id] = {
                "name": service.service_name,
                "startup_time": service.startup_time,
                "endpoint": service.endpoint,
                "readiness": service.readiness,
                "liveness": service.liveness,
                "capabilities": service.capabilities,
                "health_check_count": len(history),
                "recent_checks": recent_checks[-5:] if recent_checks else []
            }
            
        return matrix
        
    def get_health_summary(self) -> Dict[str, Any]:
        
        services = self.registry.get_all_services()
        healthy = self.registry.get_healthy_services()
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_participants": len(services),
            "healthy_participants": len(healthy),
            "unhealthy_participants": len(services) - len(healthy),
            "health_percentage": (len(healthy) / len(services) * 100) if services else 0,
            "status": "HEALTHY" if len(healthy) == len(services) else "DEGRADED"
        }


def create_service_registration(
    service_id: str,
    service_name: str,
    hostname: str,
    port: int,
    capabilities: List[Dict[str, Any]],
    readiness: bool = True,
    liveness: bool = True
) -> ServiceRegistration:
   
    
    endpoint = {
        "hostname": hostname,
        "port": port,
        "protocol": "http",
        "url": f"http://{hostname}:{port}"
    }
    
    return ServiceRegistration(
        service_id=service_id,
        service_name=service_name,
        startup_time=datetime.now(timezone.utc).isoformat(),
        endpoint=endpoint,
        capabilities=capabilities,
        health_status={
            "checks_passed": 0,
            "checks_failed": 0,
            "last_check": datetime.now(timezone.utc).isoformat()
        },
        readiness=readiness,
        liveness=liveness,
        registration_timestamp=datetime.now(timezone.utc).isoformat()
    )


def demonstrate_service_registry():
    
    registry = get_registry()
    discovery = ServiceDiscoveryClient()
    monitor = ParticipantHealthMonitor()
    
    print("\n=== SERVICE REGISTRY DEMONSTRATION ===\n")
    
    
    sanskar_reg = create_service_registration(
        service_id="sanskar-001",
        service_name="SANSKAR",
        hostname="localhost",
        port=8001,
        capabilities=[
            {"capability": "ranking_engine", "version": "v1", "status": "READY"},
            {"capability": "adaptive_intelligence", "version": "v1", "status": "READY"}
        ]
    )
    registry.register_service(sanskar_reg)
    print("✓ SANSKAR registered")
    
    
    rajya_reg = create_service_registration(
        service_id="rajya-002",
        service_name="RAJYA",
        hostname="localhost",
        port=8002,
        capabilities=[
            {"capability": "governance_validation", "version": "v1", "status": "READY"},
            {"capability": "boundary_enforcement", "version": "v1", "status": "READY"}
        ]
    )
    registry.register_service(rajya_reg)
    print("✓ RAJYA registered")
    
    
    enforcement_reg = create_service_registration(
        service_id="enforcement-003",
        service_name="ENFORCEMENT",
        hostname="localhost",
        port=8003,
        capabilities=[
            {"capability": "fail_closed_enforcement", "version": "v1", "status": "READY"},
            {"capability": "authority_validation", "version": "v1", "status": "READY"}
        ]
    )
    registry.register_service(enforcement_reg)
    print("✓ ENFORCEMENT registered\n")
    
    
    print("REGISTRY STATUS:")
    registry_status = registry.get_registry_status()
    print(json.dumps(registry_status, indent=2))
    
    
    print("\nSERVICE DISCOVERY:")
    sanskar = discovery.discover_service("SANSKAR")
    if sanskar:
        print(f"✓ Discovered SANSKAR at {sanskar.endpoint['url']}")
    
   
    print("\nNETWORK TOPOLOGY:")
    network_map = discovery.get_participant_network_map()
    print(json.dumps(network_map, indent=2))
    
    
    print("\nPARTICIPANT HEALTH MATRIX:")
    health_matrix = monitor.get_health_matrix()
    print(json.dumps(health_matrix, indent=2))
    
    
    print("\nHEALTH SUMMARY:")
    health_summary = monitor.get_health_summary()
    print(json.dumps(health_summary, indent=2))
    
    
    with open("service_registry.json", "w") as f:
        json.dump(registry_status, f, indent=2)
    
    with open("participant_health_matrix.json", "w") as f:
        json.dump(health_matrix, f, indent=2)
    
    print("\n✓ Saved service_registry.json")
    print("✓ Saved participant_health_matrix.json")
    
    return registry_status, health_matrix


if __name__ == "__main__":
    demonstrate_service_registry()
