import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import api from "../api/client";
import { Card } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Table } from "../components/ui/Table";

interface ProductionOrder {
  id: number;
  product_name: string;
  quantity: number;
  completed_quantity: number;
  status: string;
  progress: number;
}

export default function ManufacturingPage() {
  const [orders, setOrders] = useState<ProductionOrder[]>([]);

  const { data: ordersData } = useQuery({
    queryKey: ["production-orders"],
    queryFn: async () => {
      const res = await api.get("/manufacturing/production-orders/");
      return res.data;
    },
  });

  useEffect(() => {
    if (ordersData) setOrders(ordersData);
  }, [ordersData]);

  const inProgress = orders.filter((o) => o.status === "in_progress");
  const completed = orders.filter((o) => o.status === "completed");

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-semibold">Manufacturing</h1>
        <div className="space-x-2">
          <Button variant="outline">Create BOM</Button>
          <Button>New Production Order</Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <div className="text-sm text-gray-500">Total Orders</div>
          <div className="text-2xl font-bold">{orders.length}</div>
        </Card>
        <Card>
          <div className="text-sm text-gray-500">In Progress</div>
          <div className="text-2xl font-bold">{inProgress.length}</div>
        </Card>
        <Card>
          <div className="text-sm text-gray-500">Completed</div>
          <div className="text-2xl font-bold">{completed.length}</div>
        </Card>
        <Card>
          <div className="text-sm text-gray-500">Completion Rate</div>
          <div className="text-2xl font-bold">
            {orders.length > 0
              ? `${Math.round((completed.length / orders.length) * 100)}%`
              : "0%"}
          </div>
        </Card>
      </div>

      <Card>
        <h2 className="text-lg font-semibold mb-4">Active Production Orders</h2>
        <Table
          headers={["Product", "Quantity", "Progress", "Status"]}
          data={orders
            .filter((o) => o.status !== "completed")
            .map((order) => ({
              Product: order.product_name,
              Quantity: `${order.completed_quantity}/${order.quantity}`,
              Progress: (
                <div className="w-full bg-gray-200 rounded-full h-2.5">
                  <div
                    className="bg-indigo-600 h-2.5 rounded-full"
                    style={{ width: `${order.progress}%` }}
                  ></div>
                </div>
              ),
              Status: (
                <span
                  className={`px-2 py-1 text-sm rounded-full ${
                    order.status === "in_progress"
                      ? "bg-blue-100 text-blue-800"
                      : order.status === "planned"
                        ? "bg-yellow-100 text-yellow-800"
                        : "bg-gray-100 text-gray-800"
                  }`}
                >
                  {order.status}
                </span>
              ),
            }))}
        />
      </Card>
    </div>
  );
}
