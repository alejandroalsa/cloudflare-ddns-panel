<script setup lang="ts">
import { ref, onMounted } from "vue";
import { api, type User, type UserRole } from "@/lib/api";
import { useAuthStore } from "@/stores/auth";
import { useConfirm } from "@/lib/confirm";
import AppLayout from "@/components/AppLayout.vue";
import Card from "@/components/ui/Card.vue";
import CardHeader from "@/components/ui/CardHeader.vue";
import CardTitle from "@/components/ui/CardTitle.vue";
import CardDescription from "@/components/ui/CardDescription.vue";
import CardContent from "@/components/ui/CardContent.vue";
import Button from "@/components/ui/Button.vue";
import Input from "@/components/ui/Input.vue";
import PasswordInput from "@/components/ui/PasswordInput.vue";
import Label from "@/components/ui/Label.vue";
import Select from "@/components/ui/Select.vue";
import Badge from "@/components/ui/Badge.vue";
import Dialog from "@/components/ui/Dialog.vue";
import Switch from "@/components/ui/Switch.vue";
import { Plus, Trash2, CheckCircle2, Ban, Pencil, Save, X, UserPlus, ShieldCheck, Eye, Smartphone, ShieldOff } from "lucide-vue-next";

const auth = useAuthStore();
const { confirmDelete } = useConfirm();
const users = ref<User[]>([]);
const loading = ref(true);
const error = ref("");

// --- Crear usuario ---
const showCreateDialog = ref(false);
const newUsername = ref("");
const newEmail = ref("");
const newPassword = ref("");
const newRole = ref<UserRole>("viewer");
const saving = ref(false);

// --- Editar usuario existente ---
const showEditDialog = ref(false);
const editingUser = ref<User | null>(null);
const editUsername = ref("");
const editEmail = ref("");
const editPassword = ref("");
const editRole = ref<UserRole>("viewer");
const editActive = ref(true);
const savingEdit = ref(false);
const editError = ref("");

async function load() {
  loading.value = true;
  const { data } = await api.get<User[]>("/users");
  users.value = data;
  loading.value = false;
}

function resetCreateForm() {
  newUsername.value = "";
  newEmail.value = "";
  newPassword.value = "";
  newRole.value = "viewer";
}

async function createUser() {
  saving.value = true;
  error.value = "";
  try {
    await api.post("/users", {
      username: newUsername.value,
      email: newEmail.value || null,
      password: newPassword.value,
      role: newRole.value,
    });
    showCreateDialog.value = false;
    resetCreateForm();
    await load();
  } catch (e: any) {
    error.value = e?.response?.data?.detail || "No se pudo crear el usuario";
  } finally {
    saving.value = false;
  }
}

function openEditDialog(user: User) {
  editingUser.value = user;
  editUsername.value = user.username;
  editEmail.value = user.email || "";
  editPassword.value = "";
  editRole.value = user.role;
  editActive.value = user.is_active;
  editError.value = "";
  showEditDialog.value = true;
}

async function saveEdit() {
  if (!editingUser.value) return;
  savingEdit.value = true;
  editError.value = "";
  try {
    const payload: Record<string, unknown> = {
      username: editUsername.value,
      email: editEmail.value || null,
      role: editRole.value,
      is_active: editActive.value,
    };
    if (editPassword.value) payload.password = editPassword.value;
    await api.put(`/users/${editingUser.value.id}`, payload);
    showEditDialog.value = false;
    await load();
  } catch (e: any) {
    editError.value = e?.response?.data?.detail || "No se pudo actualizar el usuario";
  } finally {
    savingEdit.value = false;
  }
}

async function deleteUser(user: User) {
  const ok = await confirmDelete(
    `Eliminar a ${user.username}`,
    "Este usuario perderá el acceso al panel de forma inmediata. Esta acción no se puede deshacer."
  );
  if (!ok) return;
  await api.delete(`/users/${user.id}`);
  await load();
}

async function disable2fa(user: User) {
  const ok = await confirmDelete(
    `Desactivar 2FA de ${user.username}`,
    "El usuario podrá volver a iniciar sesión solo con su contraseña, sin código de verificación.",
    "Desactivar"
  );
  if (!ok) return;
  await api.post(`/users/${user.id}/disable-2fa`);
  await load();
}

onMounted(load);
</script>

<template>
  <AppLayout>
    <div class="mb-6 flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold">Usuarios</h1>
        <p class="text-muted-foreground">Gestión de accesos al panel</p>
      </div>
      <Button @click="showCreateDialog = true"><UserPlus class="h-4 w-4" /> Nuevo usuario</Button>
    </div>

    <Card>
      <CardHeader>
        <CardTitle>Usuarios del panel</CardTitle>
        <CardDescription>Los administradores pueden gestionar dominios y ajustes; los de solo lectura únicamente pueden consultar.</CardDescription>
      </CardHeader>
      <CardContent>
        <div v-if="loading" class="text-muted-foreground">Cargando…</div>
        <div v-else class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b text-left text-muted-foreground">
                <th class="py-2 pr-4 font-medium">Usuario</th>
                <th class="py-2 pr-4 font-medium">Email</th>
                <th class="py-2 pr-4 font-medium">Rol</th>
                <th class="py-2 pr-4 font-medium">Estado</th>
                <th class="py-2 pr-4 font-medium">2FA</th>
                <th class="py-2 pr-4 font-medium text-right">Acciones</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="user in users" :key="user.id" class="border-b last:border-0">
                <td class="py-2 pr-4 font-medium">{{ user.username }}</td>
                <td class="py-2 pr-4">{{ user.email || "—" }}</td>
                <td class="py-2 pr-4">
                  <Badge :variant="user.role === 'admin' ? 'default' : 'secondary'" class="gap-1.5">
                    <ShieldCheck v-if="user.role === 'admin'" class="h-3.5 w-3.5" />
                    <Eye v-else class="h-3.5 w-3.5" />
                    {{ user.role === "admin" ? "Admin" : "Solo lectura" }}
                  </Badge>
                </td>
                <td class="py-2 pr-4">
                  <Badge :variant="user.is_active ? 'success' : 'secondary'" class="gap-1">
                    <CheckCircle2 v-if="user.is_active" class="h-3.5 w-3.5" />
                    <Ban v-else class="h-3.5 w-3.5" />
                    {{ user.is_active ? "Activo" : "Deshabilitado" }}
                  </Badge>
                </td>
                <td class="py-2 pr-4">
                  <Badge :variant="user.totp_enabled ? 'success' : 'outline'" class="gap-1">
                    <ShieldCheck v-if="user.totp_enabled" class="h-3.5 w-3.5" />
                    <Smartphone v-else class="h-3.5 w-3.5" />
                    {{ user.totp_enabled ? "Activo" : "Inactivo" }}
                  </Badge>
                </td>
                <td class="py-2 pr-4 text-right">
                  <Button variant="ghost" size="icon" title="Editar usuario" @click="openEditDialog(user)">
                    <Pencil class="h-4 w-4" />
                  </Button>
                  <Button
                    v-if="user.totp_enabled"
                    variant="ghost"
                    size="icon"
                    title="Desactivar 2FA de este usuario"
                    @click="disable2fa(user)"
                  >
                    <ShieldOff class="h-4 w-4 text-amber-600" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    title="Eliminar usuario"
                    :disabled="user.id === auth.user?.id"
                    @click="deleteUser(user)"
                  >
                    <Trash2 class="h-4 w-4 text-destructive" />
                  </Button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>

    <!-- Diálogo: crear usuario -->
    <Dialog v-model:open="showCreateDialog">
      <h2 class="mb-4 text-lg font-semibold">Nuevo usuario</h2>
      <form class="space-y-4" @submit.prevent="createUser">
        <div class="space-y-1.5">
          <Label>Usuario</Label>
          <Input v-model="newUsername" required />
        </div>
        <div class="space-y-1.5">
          <Label>Email</Label>
          <Input v-model="newEmail" type="email" />
        </div>
        <div class="space-y-1.5">
          <Label>Contraseña</Label>
          <PasswordInput v-model="newPassword" required />
        </div>
        <div class="space-y-1.5">
          <Label>Rol</Label>
          <Select v-model="newRole">
            <option value="viewer">Solo lectura</option>
            <option value="admin">Admin</option>
          </Select>
        </div>
        <p v-if="error" class="text-sm text-destructive">{{ error }}</p>
        <div class="flex justify-end gap-2 pt-2">
          <Button type="button" variant="outline" @click="showCreateDialog = false">
            <X class="h-4 w-4" /> Cancelar
          </Button>
          <Button type="submit" :disabled="saving">
            <Save class="h-4 w-4" /> {{ saving ? "Creando..." : "Crear" }}
          </Button>
        </div>
      </form>
    </Dialog>

    <!-- Diálogo: editar usuario existente -->
    <Dialog v-model:open="showEditDialog">
      <h2 class="mb-4 text-lg font-semibold">Editar usuario</h2>
      <form class="space-y-4" @submit.prevent="saveEdit">
        <div class="space-y-1.5">
          <Label>Usuario</Label>
          <Input v-model="editUsername" required />
        </div>
        <div class="space-y-1.5">
          <Label>Email</Label>
          <Input v-model="editEmail" type="email" />
        </div>
        <div class="space-y-1.5">
          <Label>Nueva contraseña</Label>
          <PasswordInput v-model="editPassword" placeholder="Dejar en blanco para no cambiarla" />
        </div>
        <div class="space-y-1.5">
          <Label>Rol</Label>
          <Select v-model="editRole" :disabled="editingUser?.id === auth.user?.id">
            <option value="viewer">Solo lectura</option>
            <option value="admin">Admin</option>
          </Select>
        </div>
        <div class="flex items-center justify-between gap-3 rounded-[5px] border px-3 py-2">
          <div class="min-w-0">
            <p class="text-sm font-medium">Cuenta activa</p>
            <p class="text-xs text-muted-foreground">Si se desactiva, el usuario no podrá iniciar sesión.</p>
          </div>
          <Switch v-model="editActive" :disabled="editingUser?.id === auth.user?.id" class="shrink-0" />
        </div>
        <p v-if="editError" class="text-sm text-destructive">{{ editError }}</p>
        <div class="flex justify-end gap-2 pt-2">
          <Button type="button" variant="outline" @click="showEditDialog = false">
            <X class="h-4 w-4" /> Cancelar
          </Button>
          <Button type="submit" :disabled="savingEdit">
            <Save class="h-4 w-4" /> {{ savingEdit ? "Guardando..." : "Guardar" }}
          </Button>
        </div>
      </form>
    </Dialog>
  </AppLayout>
</template>
