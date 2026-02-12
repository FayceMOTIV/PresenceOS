"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { formatNumber } from "@/lib/utils";

interface PlatformChartProps {
  data: Array<{
    name: string;
    impressions: number;
    engagement: number;
  }>;
}

export default function PlatformChart({ data }: PlatformChartProps) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data}>
        <XAxis dataKey="name" />
        <YAxis />
        <Tooltip
          formatter={(value: number) => formatNumber(value)}
          contentStyle={{
            backgroundColor: "hsl(var(--background))",
            border: "1px solid hsl(var(--border))",
            borderRadius: "8px",
          }}
        />
        <Bar dataKey="impressions" fill="#8b5cf6" radius={[8, 8, 0, 0]} />
        <Bar dataKey="engagement" fill="#06b6d4" radius={[8, 8, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
