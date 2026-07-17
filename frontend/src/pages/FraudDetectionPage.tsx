import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import api from "../api/client";
import { Card } from "../components/ui/Card";
import { Table } from "../components/ui/Table";
import { AlertTriangle, Shield, TrendingUp, Activity } from "lucide-react";

interface FraudMetrics {
  risk_score: number;
  sales_anomalies: any[];
  inventory_anomalies: any[];
  fraud_patterns: any[];
}

export default function FraudDetectionPage() {
  const [metrics, setMetrics] = useState<FraudMetrics | null>(null);

  const { data: fraudData } = useQuery({
    queryKey: ["fraud-detection"],
    queryFn: async () => {
      const res = await api.get("/fraud/detect/");
      return res.data;
    },
  });

  const { data: metricsData } = useQuery({
    queryKey: ["fraud-metrics"],
    queryFn: async () => {
      const res = await api.get("/fraud/metrics/");
      return res.data;
    },
  });

  useEffect(() => {
    if (fraudData) setMetrics(fraudData);
  }, [fraudData]);

  const getRiskColor = (score: number) => {
    if (score < 30) return "text-green-600";
    if (score < 60) return "text-yellow-600";
    return "text-red-600";
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-semibold">Fraud Detection</h1>
        <div className="flex items-center space-x-2">
          <Activity className="h-4 w-4 text-gray-500" />
          <span className="text-sm text-gray-500">Real-time monitoring</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Shield className="h-5 w-5 text-indigo-600" />
              <div className="text-sm text-gray-500">Risk Score</div>
            </div>
            <div
              className={`text-2xl font-bold ${getRiskColor(metrics?.risk_score || 0)}`}
            >
              {metrics?.risk_score || 0}/100
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center space-x-2">
            <AlertTriangle className="h-5 w-5 text-yellow-600" />
            <div>
              <div className="text-sm text-gray-500">Suspicious Activities</div>
              <div className="text-2xl font-bold">
                {(metrics?.sales_anomalies?.length || 0) +
                  (metrics?.inventory_anomalies?.length || 0) +
                  (metrics?.fraud_patterns?.length || 0)}
              </div>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center space-x-2">
            <TrendingUp className="h-5 w-5 text-blue-600" />
            <div>
              <div className="text-sm text-gray-500">Alert Level</div>
              <div
                className={`text-2xl font-bold ${
                  (metrics?.sales_anomalies?.length || 0) > 5
                    ? "text-red-600"
                    : "text-green-600"
                }`}
              >
                {(metrics?.sales_anomalies?.length || 0) > 5
                  ? "🚨 High"
                  : "✅ Normal"}
              </div>
            </div>
          </div>
        </Card>
      </div>

      {metrics?.sales_anomalies && metrics.sales_anomalies.length > 0 && (
        <Card>
          <h2 className="text-lg font-semibold mb-4 flex items-center">
            <AlertTriangle className="h-5 w-5 text-yellow-600 mr-2" />
            Sales Anomalies Detected
          </h2>
          <Table
            headers={["Sale ID", "Total", "Date", "Confidence"]}
            data={metrics.sales_anomalies.map((anomaly: any) => ({
              "Sale ID": anomaly.sale_id,
              Total: `$${anomaly.total.toFixed(2)}`,
              Date: new Date(anomaly.date).toLocaleDateString(),
              Confidence: `${(Math.abs(anomaly.confidence) * 100).toFixed(1)}%`,
            }))}
          />
        </Card>
      )}

      {metrics?.fraud_patterns && metrics.fraud_patterns.length > 0 && (
        <Card>
          <h2 className="text-lg font-semibold mb-4 flex items-center">
            <Shield className="h-5 w-5 text-red-600 mr-2" />
            Fraud Patterns
          </h2>
          <Table
            headers={["Pattern", "Severity", "Details"]}
            data={metrics.fraud_patterns.map((pattern: any) => ({
              Pattern: pattern.pattern,
              Severity: (
                <span
                  className={`px-2 py-1 text-sm rounded-full ${
                    pattern.severity === "high"
                      ? "bg-red-100 text-red-800"
                      : pattern.severity === "medium"
                        ? "bg-yellow-100 text-yellow-800"
                        : "bg-blue-100 text-blue-800"
                  }`}
                >
                  {pattern.severity}
                </span>
              ),
              Details: JSON.stringify(pattern),
            }))}
          />
        </Card>
      )}
    </div>
  );
}
