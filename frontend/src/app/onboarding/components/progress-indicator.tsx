"use client";

import { cn } from "@/lib/utils";
import { Check } from "lucide-react";
import { motion } from "framer-motion";

interface Step {
  id: number;
  title: string;
  description: string;
}

interface ProgressIndicatorProps {
  steps: Step[];
  currentStep: number;
}

export function ProgressIndicator({ steps, currentStep }: ProgressIndicatorProps) {
  return (
    <div className="relative">
      {/* Desktop version */}
      <div className="hidden md:flex items-center justify-between">
        {steps.map((step, index) => {
          const isCompleted = step.id < currentStep;
          const isCurrent = step.id === currentStep;

          return (
            <div key={step.id} className="flex-1 flex items-center">
              {/* Step circle */}
              <div className="flex flex-col items-center relative">
                <motion.div
                  initial={false}
                  animate={{
                    scale: isCurrent ? 1.1 : 1,
                    backgroundColor: isCompleted
                      ? "hsl(var(--primary))"
                      : isCurrent
                      ? "hsl(var(--primary))"
                      : "hsl(var(--muted))",
                  }}
                  className={cn(
                    "w-10 h-10 rounded-full flex items-center justify-center text-sm font-medium transition-all",
                    isCompleted || isCurrent
                      ? "text-primary-foreground"
                      : "text-muted-foreground"
                  )}
                >
                  {isCompleted ? (
                    <Check className="w-5 h-5" />
                  ) : (
                    <span>{step.id}</span>
                  )}
                </motion.div>

                {/* Label */}
                <div className="absolute top-12 text-center whitespace-nowrap">
                  <p
                    className={cn(
                      "text-sm font-medium",
                      isCurrent ? "text-foreground" : "text-muted-foreground"
                    )}
                  >
                    {step.title}
                  </p>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    {step.description}
                  </p>
                </div>
              </div>

              {/* Connector line */}
              {index < steps.length - 1 && (
                <div className="flex-1 h-0.5 mx-4 bg-muted overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{
                      width: isCompleted ? "100%" : "0%",
                    }}
                    transition={{ duration: 0.3 }}
                    className="h-full bg-primary"
                  />
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Mobile version */}
      <div className="md:hidden">
        <div className="flex items-center justify-between mb-4">
          {steps.map((step) => {
            const isCompleted = step.id < currentStep;
            const isCurrent = step.id === currentStep;

            return (
              <div key={step.id} className="flex-1 flex justify-center">
                <motion.div
                  initial={false}
                  animate={{
                    scale: isCurrent ? 1.15 : 1,
                    backgroundColor: isCompleted
                      ? "hsl(var(--primary))"
                      : isCurrent
                      ? "hsl(var(--primary))"
                      : "hsl(var(--muted))",
                  }}
                  className={cn(
                    "w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium",
                    isCompleted || isCurrent
                      ? "text-primary-foreground"
                      : "text-muted-foreground"
                  )}
                >
                  {isCompleted ? <Check className="w-4 h-4" /> : step.id}
                </motion.div>
              </div>
            );
          })}
        </div>

        {/* Current step info */}
        <div className="text-center">
          <p className="font-medium">{steps[currentStep - 1]?.title}</p>
          <p className="text-sm text-muted-foreground">
            {steps[currentStep - 1]?.description}
          </p>
        </div>
      </div>
    </div>
  );
}
