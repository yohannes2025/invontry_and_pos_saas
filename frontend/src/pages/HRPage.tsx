import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import api from "../api/client";
import { Card } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Table } from "../components/ui/Table";

interface Employee {
  id: number;
  employee_id: string;
  full_name: string;
  department: string;
  employment_type: string;
  is_active: boolean;
}

export default function HRPage() {
  const [employees, setEmployees] = useState<Employee[]>([]);

  const { data: employeesData } = useQuery({
    queryKey: ["employees"],
    queryFn: async () => {
      const res = await api.get("/hr/employees/");
      return res.data;
    },
  });

  useEffect(() => {
    if (employeesData) setEmployees(employeesData);
  }, [employeesData]);

  const activeEmployees = employees.filter((e) => e.is_active);
  const departments = [...new Set(employees.map((e) => e.department))];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-semibold">HR Management</h1>
        <div className="space-x-2">
          <Button variant="outline">Clock In</Button>
          <Button>Add Employee</Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <div className="text-sm text-gray-500">Total Employees</div>
          <div className="text-2xl font-bold">{employees.length}</div>
        </Card>
        <Card>
          <div className="text-sm text-gray-500">Active Employees</div>
          <div className="text-2xl font-bold">{activeEmployees.length}</div>
        </Card>
        <Card>
          <div className="text-sm text-gray-500">Departments</div>
          <div className="text-2xl font-bold">{departments.length}</div>
        </Card>
        <Card>
          <div className="text-sm text-gray-500">On Leave Today</div>
          <div className="text-2xl font-bold">3</div>
        </Card>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <h2 className="text-lg font-semibold mb-4">
            Department Distribution
          </h2>
          <div className="space-y-2">
            {departments.map((dept) => (
              <div key={dept} className="flex justify-between items-center">
                <span>{dept}</span>
                <span className="font-semibold">
                  {
                    employees.filter(
                      (e) => e.department === dept && e.is_active,
                    ).length
                  }
                </span>
              </div>
            ))}
          </div>
        </Card>

        <Card>
          <h2 className="text-lg font-semibold mb-4">Recent Leave Requests</h2>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span>John Doe</span>
              <span className="text-yellow-600">Pending</span>
            </div>
            <div className="flex justify-between">
              <span>Jane Smith</span>
              <span className="text-green-600">Approved</span>
            </div>
            <div className="flex justify-between">
              <span>Bob Johnson</span>
              <span className="text-red-600">Rejected</span>
            </div>
          </div>
        </Card>
      </div>

      <Card>
        <h2 className="text-lg font-semibold mb-4">Employee List</h2>
        <Table
          headers={["ID", "Name", "Department", "Type", "Status"]}
          data={employees.map((emp) => ({
            ID: emp.employee_id,
            Name: emp.full_name,
            Department: emp.department,
            Type: emp.employment_type,
            Status: emp.is_active ? "✅ Active" : "❌ Inactive",
          }))}
        />
      </Card>
    </div>
  );
}
