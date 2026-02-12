"use client";

import { useState } from "react";
import {
  ColumnFiltersState,
  SortingState,
  VisibilityState,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { motion, AnimatePresence } from "framer-motion";
import { Search, Trash2, Send, X } from "lucide-react";

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
import { ScheduledPost, SocialConnector } from "@/types";
import { createPostsColumns } from "./posts-columns";
import { PostsFiltersComponent, PostsFilters } from "./posts-filters";

interface PostsTableProps {
  posts: ScheduledPost[];
  connectors: SocialConnector[];
  filters: PostsFilters;
  onFiltersChange: (filters: PostsFilters) => void;
  onView: (post: ScheduledPost) => void;
  onEdit: (post: ScheduledPost) => void;
  onDuplicate: (post: ScheduledPost) => void;
  onDelete: (post: ScheduledPost) => void;
  onPublishNow: (post: ScheduledPost) => void;
  onBulkDelete: (posts: ScheduledPost[]) => void;
  onBulkPublish: (posts: ScheduledPost[]) => void;
}

export function PostsTable({
  posts,
  connectors,
  filters,
  onFiltersChange,
  onView,
  onEdit,
  onDuplicate,
  onDelete,
  onPublishNow,
  onBulkDelete,
  onBulkPublish,
}: PostsTableProps) {
  const [sorting, setSorting] = useState<SortingState>([
    { id: "scheduled_at", desc: false },
  ]);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
  const [columnVisibility, setColumnVisibility] = useState<VisibilityState>({});
  const [rowSelection, setRowSelection] = useState({});
  const [globalFilter, setGlobalFilter] = useState("");

  const columns = createPostsColumns({
    connectors,
    onView,
    onEdit,
    onDuplicate,
    onDelete,
    onPublishNow,
  });

  const table = useReactTable({
    data: posts,
    columns,
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    onColumnVisibilityChange: setColumnVisibility,
    onRowSelectionChange: setRowSelection,
    onGlobalFilterChange: setGlobalFilter,
    globalFilterFn: "includesString",
    state: {
      sorting,
      columnFilters,
      columnVisibility,
      rowSelection,
      globalFilter,
    },
  });

  const selectedRows = table.getFilteredSelectedRowModel().rows;
  const selectedPosts = selectedRows.map((row) => row.original);
  const hasSelection = selectedRows.length > 0;

  // Check if any selected post can be published
  const canPublishSelected = selectedPosts.some(
    (p) => p.status === "scheduled" || p.status === "failed"
  );

  // Check if any selected post can be deleted
  const canDeleteSelected = selectedPosts.some(
    (p) => p.status !== "publishing"
  );

  const clearSelection = () => {
    setRowSelection({});
  };

  return (
    <div className="space-y-4">
      {/* Search and Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Rechercher un post..."
            value={globalFilter}
            onChange={(e) => setGlobalFilter(e.target.value)}
            className="pl-9"
          />
        </div>
        <PostsFiltersComponent
          filters={filters}
          onFiltersChange={onFiltersChange}
        />
      </div>

      {/* Bulk Actions Bar */}
      <AnimatePresence>
        {hasSelection && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="flex items-center gap-3 p-3 bg-muted/50 rounded-lg border"
          >
            <span className="text-sm font-medium">
              {selectedRows.length} post{selectedRows.length > 1 ? "s" : ""} selectionne{selectedRows.length > 1 ? "s" : ""}
            </span>
            <div className="flex-1" />
            <div className="flex items-center gap-2">
              {canPublishSelected && (
                <Button
                  size="sm"
                  variant="outline"
                  className="gap-2 text-green-600 hover:text-green-700 hover:bg-green-50 dark:hover:bg-green-950"
                  onClick={() => {
                    const publishablePosts = selectedPosts.filter(
                      (p) => p.status === "scheduled" || p.status === "failed"
                    );
                    onBulkPublish(publishablePosts);
                    clearSelection();
                  }}
                >
                  <Send className="w-4 h-4" />
                  Publier
                </Button>
              )}
              {canDeleteSelected && (
                <Button
                  size="sm"
                  variant="outline"
                  className="gap-2 text-destructive hover:text-destructive hover:bg-destructive/10"
                  onClick={() => {
                    const deletablePosts = selectedPosts.filter(
                      (p) => p.status !== "publishing"
                    );
                    onBulkDelete(deletablePosts);
                    clearSelection();
                  }}
                >
                  <Trash2 className="w-4 h-4" />
                  Supprimer
                </Button>
              )}
              <Button
                size="sm"
                variant="ghost"
                onClick={clearSelection}
              >
                <X className="w-4 h-4" />
              </Button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Table */}
      <div className="rounded-md border">
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
                  className="cursor-pointer"
                  onClick={() => onView(row.original)}
                >
                  {row.getVisibleCells().map((cell) => (
                    <TableCell
                      key={cell.id}
                      onClick={(e) => {
                        // Prevent row click for checkbox and actions
                        if (
                          cell.column.id === "select" ||
                          cell.column.id === "actions"
                        ) {
                          e.stopPropagation();
                        }
                      }}
                    >
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
                  className="h-24 text-center"
                >
                  Aucun post trouve.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between">
        <div className="text-sm text-muted-foreground">
          {table.getFilteredRowModel().rows.length} post{table.getFilteredRowModel().rows.length !== 1 ? "s" : ""}
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
          >
            Precedent
          </Button>
          <div className="text-sm">
            Page {table.getState().pagination.pageIndex + 1} sur{" "}
            {table.getPageCount() || 1}
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
          >
            Suivant
          </Button>
        </div>
      </div>
    </div>
  );
}
