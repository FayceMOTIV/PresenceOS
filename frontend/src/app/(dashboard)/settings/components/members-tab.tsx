"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { UserPlus, Trash2, Loader2, Shield, Crown, User as UserIcon, Mail } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "@/hooks/use-toast";
import { workspacesApi } from "@/lib/api";
import { WorkspaceMember, UserRole } from "@/types";

interface MembersTabProps {
  workspaceId: string | null;
  userRole: UserRole;
  currentUserId?: string;
}

export function MembersTab({ workspaceId, userRole, currentUserId }: MembersTabProps) {
  const [members, setMembers] = useState<WorkspaceMember[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState<string>("member");
  const [isInviting, setIsInviting] = useState(false);
  const canManage = userRole === "owner" || userRole === "admin";

  useEffect(() => {
    const fetchMembers = () => {
      if (!workspaceId) {
        setIsLoading(false);
        return;
      }
      workspacesApi.getMembers(workspaceId)
        .then((res) => {
          setMembers(res.data || []);
        })
        .catch(() => {
          toast({
            title: "Erreur",
            description: "Impossible de charger les membres",
            variant: "destructive"
          });
        })
        .finally(() => setIsLoading(false));
    };

    fetchMembers();
  }, [workspaceId]);

  const fetchMembers = () => {
    if (!workspaceId) return;
    workspacesApi.getMembers(workspaceId)
      .then((res) => {
        setMembers(res.data || []);
      })
      .catch(() => {
        toast({
          title: "Erreur",
          description: "Impossible de charger les membres",
          variant: "destructive"
        });
      });
  };

  const handleInvite = async () => {
    if (!workspaceId) return;
    if (!inviteEmail.trim()) {
      toast({
        title: "Erreur",
        description: "L'email est requis",
        variant: "destructive"
      });
      return;
    }

    setIsInviting(true);
    try {
      await workspacesApi.inviteMember(workspaceId, {
        email: inviteEmail.trim(),
        role: inviteRole
      });
      toast({ title: "Invitation envoyee" });
      setInviteEmail("");
      setInviteRole("member");
      fetchMembers();
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || "Impossible d'inviter le membre";
      toast({
        title: "Erreur",
        description: errorMsg,
        variant: "destructive"
      });
    } finally {
      setIsInviting(false);
    }
  };

  const handleRoleChange = async (memberId: string, userId: string, newRole: string) => {
    if (!workspaceId) return;
    try {
      await workspacesApi.updateMemberRole(workspaceId, userId, newRole);
      toast({ title: "Role mis a jour" });
      fetchMembers();
    } catch (error: any) {
      toast({
        title: "Erreur",
        description: error.response?.data?.detail || "Impossible de modifier le role",
        variant: "destructive"
      });
    }
  };

  const handleRemove = async (userId: string) => {
    if (!workspaceId) return;
    try {
      await workspacesApi.removeMember(workspaceId, userId);
      toast({ title: "Membre retire" });
      fetchMembers();
    } catch (error: any) {
      toast({
        title: "Erreur",
        description: error.response?.data?.detail || "Impossible de retirer le membre",
        variant: "destructive"
      });
    }
  };

  const getRoleIcon = (role: UserRole) => {
    if (role === "owner") return <Crown className="w-4 h-4 text-amber-500" />;
    if (role === "admin") return <Shield className="w-4 h-4 text-violet-500" />;
    return <UserIcon className="w-4 h-4 text-gray-500" />;
  };

  const getRoleBadgeVariant = (role: UserRole) => {
    if (role === "owner") return "default";
    if (role === "admin") return "secondary";
    return "outline";
  };

  const getRoleBadgeClass = (role: UserRole) => {
    if (role === "owner") return "bg-amber-500 hover:bg-amber-600 text-white";
    if (role === "admin") return "bg-violet-500 hover:bg-violet-600 text-white";
    return "bg-gray-500 hover:bg-gray-600 text-white";
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-48" />
            <Skeleton className="h-4 w-96" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-32 w-full" />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-48" />
          </CardHeader>
          <CardContent className="space-y-3">
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-16 w-full" />
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Invite Form - Only for Owner/Admin */}
      {canManage && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <UserPlus className="w-5 h-5" />
                Inviter un membre
              </CardTitle>
              <CardDescription>
                Ajoutez des membres a votre espace de travail
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col sm:flex-row gap-3">
                <div className="flex-1 space-y-2">
                  <Label htmlFor="inviteEmail" className="sr-only">Email</Label>
                  <Input
                    id="inviteEmail"
                    type="email"
                    placeholder="email@exemple.com"
                    value={inviteEmail}
                    onChange={(e) => setInviteEmail(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") handleInvite();
                    }}
                  />
                </div>
                <div className="w-full sm:w-40 space-y-2">
                  <Label htmlFor="inviteRole" className="sr-only">Role</Label>
                  <Select value={inviteRole} onValueChange={setInviteRole}>
                    <SelectTrigger id="inviteRole">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="member">Membre</SelectItem>
                      <SelectItem value="admin">Administrateur</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <Button
                  onClick={handleInvite}
                  disabled={isInviting}
                  className="bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-700 hover:to-purple-700"
                >
                  {isInviting ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Envoi...
                    </>
                  ) : (
                    <>
                      <UserPlus className="w-4 h-4 mr-2" />
                      Inviter
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Members List */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, delay: canManage ? 0.1 : 0 }}
      >
        <Card>
          <CardHeader>
            <CardTitle>Membres de l&apos;espace ({members.length})</CardTitle>
            <CardDescription>
              Gerez les membres et leurs roles
            </CardDescription>
          </CardHeader>
          <CardContent>
            {members.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                Aucun membre trouve
              </div>
            ) : (
              <div className="space-y-3">
                {members.map((member) => {
                  const isCurrentUser = member.user_id === currentUserId;
                  const isOwner = member.role === "owner";
                  const canChangeRole = canManage && !isOwner && !isCurrentUser;
                  const canRemove = canManage && !isOwner && !isCurrentUser;

                  return (
                    <motion.div
                      key={member.id}
                      initial={{ opacity: 0, y: 5 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="flex items-center justify-between p-4 rounded-lg border bg-card hover:bg-accent/5 transition-colors"
                    >
                      <div className="flex items-center gap-4 flex-1">
                        {/* Avatar */}
                        <div className="relative">
                          {member.user.avatar_url ? (
                            <img
                              src={member.user.avatar_url}
                              alt={member.user.full_name}
                              className="w-12 h-12 rounded-full object-cover border-2"
                            />
                          ) : (
                            <div className="w-12 h-12 rounded-full bg-gradient-to-br from-violet-500 to-purple-500 flex items-center justify-center text-white font-semibold text-lg border-2">
                              {member.user.full_name.charAt(0).toUpperCase()}
                            </div>
                          )}
                          {isCurrentUser && (
                            <div className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-green-500 border-2 border-background" />
                          )}
                        </div>

                        {/* User Info */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <p className="font-medium truncate">
                              {member.user.full_name}
                              {isCurrentUser && (
                                <span className="text-muted-foreground ml-2">(Vous)</span>
                              )}
                            </p>
                          </div>
                          <div className="flex items-center gap-2 text-sm text-muted-foreground">
                            <Mail className="w-3 h-3" />
                            <span className="truncate">{member.user.email}</span>
                          </div>
                        </div>

                        {/* Role Badge/Select */}
                        <div className="flex items-center gap-2">
                          {canChangeRole ? (
                            <Select
                              value={member.role}
                              onValueChange={(value) =>
                                handleRoleChange(member.id, member.user_id, value)
                              }
                            >
                              <SelectTrigger className="w-40">
                                <div className="flex items-center gap-2">
                                  {getRoleIcon(member.role)}
                                  <SelectValue />
                                </div>
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="member">
                                  <div className="flex items-center gap-2">
                                    <UserIcon className="w-4 h-4" />
                                    Membre
                                  </div>
                                </SelectItem>
                                <SelectItem value="admin">
                                  <div className="flex items-center gap-2">
                                    <Shield className="w-4 h-4" />
                                    Administrateur
                                  </div>
                                </SelectItem>
                              </SelectContent>
                            </Select>
                          ) : (
                            <Badge className={getRoleBadgeClass(member.role)}>
                              <span className="flex items-center gap-1">
                                {getRoleIcon(member.role)}
                                {member.role === "owner" && "Proprietaire"}
                                {member.role === "admin" && "Administrateur"}
                                {member.role === "member" && "Membre"}
                              </span>
                            </Badge>
                          )}
                        </div>
                      </div>

                      {/* Remove Button */}
                      {canRemove && (
                        <div className="ml-4">
                          <AlertDialog>
                            <AlertDialogTrigger asChild>
                              <Button
                                size="sm"
                                variant="ghost"
                                className="text-red-500 hover:text-red-600 hover:bg-red-50"
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            </AlertDialogTrigger>
                            <AlertDialogContent>
                              <AlertDialogHeader>
                                <AlertDialogTitle>
                                  Retirer ce membre ?
                                </AlertDialogTitle>
                                <AlertDialogDescription>
                                  Voulez-vous retirer <strong>{member.user.full_name}</strong> de l&apos;espace de travail ?
                                  Cette action ne peut pas etre annulee.
                                </AlertDialogDescription>
                              </AlertDialogHeader>
                              <AlertDialogFooter>
                                <AlertDialogCancel>Annuler</AlertDialogCancel>
                                <AlertDialogAction
                                  onClick={() => handleRemove(member.user_id)}
                                  className="bg-red-500 hover:bg-red-600"
                                >
                                  Retirer
                                </AlertDialogAction>
                              </AlertDialogFooter>
                            </AlertDialogContent>
                          </AlertDialog>
                        </div>
                      )}
                    </motion.div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}
