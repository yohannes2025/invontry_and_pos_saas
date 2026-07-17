import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import api from "../api/client";
import { Card } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Table } from "../components/ui/Table";

interface Vehicle {
  id: number;
  license_plate: string;
  vehicle_type: string;
  assigned_driver: number;
  is_active: boolean;
}

interface DeliveryRoute {
  id: number;
  route_name: string;
  status: string;
  total_stops: number;
  completed_stops: number;
}

export default function LogisticsPage() {
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [routes, setRoutes] = useState<DeliveryRoute[]>([]);

  const { data: vehiclesData } = useQuery({
    queryKey: ["vehicles"],
    queryFn: async () => {
      const res = await api.get("/logistics/vehicles/");
      return res.data;
    },
  });

  const { data: routesData } = useQuery({
    queryKey: ["routes"],
    queryFn: async () => {
      const res = await api.get("/logistics/routes/");
      return res.data;
    },
  });

  useEffect(() => {
    if (vehiclesData) setVehicles(vehiclesData);
    if (routesData) setRoutes(routesData);
  }, [vehiclesData, routesData]);

  const activeVehicles = vehicles.filter((v) => v.is_active);
  const inProgressRoutes = routes.filter((r) => r.status === "in_progress");

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-semibold">Logistics Management</h1>
        <Button>Create Delivery Route</Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <div className="text-sm text-gray-500">Total Vehicles</div>
          <div className="text-2xl font-bold">{vehicles.length}</div>
        </Card>
        <Card>
          <div className="text-sm text-gray-500">Active Vehicles</div>
          <div className="text-2xl font-bold">{activeVehicles.length}</div>
        </Card>
        <Card>
          <div className="text-sm text-gray-500">Active Routes</div>
          <div className="text-2xl font-bold">{inProgressRoutes.length}</div>
        </Card>
        <Card>
          <div className="text-sm text-gray-500">Route Progress</div>
          <div className="text-2xl font-bold">
            {routes.length > 0
              ? `${Math.round((routes.reduce((acc, r) => acc + r.completed_stops / r.total_stops, 0) / routes.length) * 100)}%`
              : "0%"}
          </div>
        </Card>
      </div>

      <Card>
        <h2 className="text-lg font-semibold mb-4">Active Routes</h2>
        <Table
          headers={["Route Name", "Status", "Stops", "Progress"]}
          data={routes
            .filter((r) => r.status !== "completed")
            .map((route) => ({
              "Route Name": route.route_name,
              Status: route.status,
              Stops: `${route.completed_stops}/${route.total_stops}`,
              Progress: (
                <div className="w-full bg-gray-200 rounded-full h-2.5">
                  <div
                    className="bg-indigo-600 h-2.5 rounded-full"
                    style={{
                      width: `${(route.completed_stops / route.total_stops) * 100}%`,
                    }}
                  ></div>
                </div>
              ),
            }))}
        />
      </Card>

      <Card>
        <h2 className="text-lg font-semibold mb-4">Fleet Status</h2>
        <Table
          headers={["License Plate", "Type", "Driver", "Status"]}
          data={vehicles.map((vehicle) => ({
            "License Plate": vehicle.license_plate,
            Type: vehicle.vehicle_type,
            Driver: vehicle.assigned_driver
              ? `Driver #${vehicle.assigned_driver}`
              : "Unassigned",
            Status: vehicle.is_active ? "✅ Active" : "❌ Inactive",
          }))}
        />
      </Card>
    </div>
  );
}
