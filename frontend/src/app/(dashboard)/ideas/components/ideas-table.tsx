"use client";

import { useMemo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Check, X } from "lucide-react";
import {
  ColumnDef,
  flexRender,
  getCoreRowModel,
  useReactTable,
  getPaginationRowModel,
  getSortedRowModel,
  SortingState,
  getFilteredRowModel,
  ColumnFiltersState,
  RowSelectionState,
} from "@tanstack/react-table";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ChevronLeft, ChevronRight, Search } from "lucide-react";
import { ContentIdea } from "@/types";
import { createColumns } from "./columns";
import { cn } from "@/lib/utils";

interface IdeasTableProps {
  ideas: ContentIdea[];
  onApprove: (idea: ContentIdea) => void;
  onReject: (idea: ContentIdea) => void;
  onEdit: (idea: ContentIdea) => void;
  onConvertToDraft: (idea: ContentIdea) => void;
  onBulkApprove: (ideas: ContentIdea[]) => void;
  onBulkReject: (ideas: ContentIdea[]) => void;
}

export function IdeasTable({
  ideas,
  onApprove,
  onReject,
  onEdit,
  onConvertToDraft,
  onBulkApprove,
  onBulkReject,
}: IdeasTableProps) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
  const [rowSelection, setRowSelection] = useState<RowSelectionState>({});

  const columns = useMemo(
    () =>
      createColumns({
        onApprove,
        onReject,
        onEdit,
        onConvertToDraft,
      }),
    [onApprove, onReject, onEdit, onConvertToDraft]
  );

  const table = useReactTable({
    data: ideas,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    onRowSelectionChange: setRowSelection,
    state: {
      sorting,
      columnFilters,
      rowSelection,
    },
  });

  const selectedRows = table.getFilteredSelectedRowModel().rows;
  const selectedIdeas = selectedRows.map((row) => row.original);
  const canBulkApprove = selectedIdeas.some((idea) => idea.status === "new");
  const canBulkReject = selectedIdeas.some(
    (idea) => idea.status === "new" || idea.status === "approved"
  );

  const handleBulkApprove = () => {
    const approvableIdeas = selectedIdeas.filter((idea) => idea.status === "new");
    onBulkApprove(approvableIdeas);
    setRowSelection({});
  };

  const handleBulkReject = () => {
    const rejectableIdeas = selectedIdeas.filter(
      (idea) => idea.status === "new" || idea.status === "approved"
    );
    onBulkReject(rejectableIdeas);
    setRowSelection({});
  };

  return (
    <div className="space-y-4">
      {/* Search and bulk actions */}
      <div className="flex items-center justify-between gap-4">
        <div className="relative max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Rechercher une idee..."
            value={(table.getColumn("title")?.getFilterValue() as string) ?? ""}
            onChange={(event) =>
              table.getColumn("title")?.setFilterValue(event.target.value)
            }
            className="pl-9"
          />
        </div>

        {/* Bulk actions bar */}
        <AnimatePresence>
          {selectedRows.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="flex items-center gap-2"
            >
              <span className="text-sm text-muted-foreground">
                {selectedRows.length} selectionne(s)
              </span>
              {canBulkApprove && (
                <Button
                  size="sm"
                  variant="outline"
                  className="gap-1 text-green-600 border-green-600 hover:bg-green-50"
                  onClick={handleBulkApprove}
                >
                  <Check className="w-4 h-4" />
                  Approuver ({selectedIdeas.filter((i) => i.status === "new").length})
                </Button>
              )}
              {canBulkReject && (
                <Button
                  size="sm"
                  variant="outline"
                  className="gap-1 text-red-600 border-red-600 hover:bg-red-50"
                  onClick={handleBulkReject}
                >
                  <X className="w-4 h-4" />
                  Rejeter ({selectedIdeas.filter((i) => i.status === "new" || i.status === "approved").length})
                </Button>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Table */}
      <div className="rounded-lg border bg-card">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <TableHead key={header.id}>
                    {header.isPlaceholder
                      ? null
                      : flexRender(
                          header.column.columnDef.header,
                          header.getContext()
                        )}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {table.getRowModel().rows?.length ? (
              table.getRowModel().rows.map((row) => (
                <TableRow
                  key={row.id}
                  data-state={row.getIsSelected() && "selected"}
                  className={cn(
                    row.original.status === "rejected" && "opacity-50"
                  )}
                >
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id}>
                      {flexRender(
                        cell.column.columnDef.cell,
                        cell.getContext()
                      )}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell
                  colSpan={columns.length}
                  className="h-24 text-center text-muted-foreground"
                >
                  Aucun resultat.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          {table.getFilteredRowModel().rows.length} idee(s)
        </p>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
          >
            <ChevronLeft className="w-4 h-4" />
          </Button>
          <span className="text-sm text-muted-foreground">
            Page {table.getState().pagination.pageIndex + 1} sur{" "}
            {table.getPageCount() || 1}
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
          >
            <ChevronRight className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
