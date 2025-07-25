<script lang="ts" setup>
import { useUserStore } from '@/stores/user';
import { computed, ref } from 'vue';

const userStore = useUserStore();

const email = ref('');
const password = ref('');
const isLoginMode = ref(true);
const error = ref('');

function add_sep(num: number) {
    let result = "";
    while (true) {
        const last_three = (num % 1000).toString();
        num = Math.floor(num / 1000);
        if (!(num > 0)) {
            result = last_three + result;
            break;
        } else {
            result = "," + last_three.padStart(3, "0") + result;
        }
    }
    return result;
}

const userInfo = computed(() => [
    { label: '用户名', value: userStore.user.name },
    { label: '用户ID', value: userStore.user.id },
    { label: '邮箱', value: userStore.user.email },
    { label: '余额', value: add_sep(userStore.user.balance), isBalance: true },
    { label: '历史花费', value: add_sep(userStore.user.total_spent) },
    { label: '角色', value: userStore.user.role, isRole: true },
]);

async function handleAuth() {
    error.value = '';
    try {
        if (isLoginMode.value) {
            await userStore.login(email.value, password.value);
        } else {
            await userStore.register(email.value, password.value);
        }
    } catch (err) {
        error.value = err instanceof Error ? err.message : '操作失败';
    }
}

function handleLogout() {
    userStore.logout();
}
</script>

<template>
    <main class="p-4 flex flex-col items-center">
        <section v-if="userStore.user.role === 'guest'" class="w-full max-w-md bg-white rounded-lg shadow-md p-6">
            <div class="text-center mb-6">
                <h2 class="text-2xl font-bold">{{ isLoginMode ? '用户登录' : '用户注册' }}</h2>
            </div>

            <form @submit.prevent="handleAuth" class="space-y-4">
                <div>
                    <label class="block text-sm font-medium text-secondary-500 mb-1">邮箱</label>
                    <input v-model="email" type="email" required
                        class="w-full px-3 py-2 border border-secondary-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500">
                </div>

                <div>
                    <label class="block text-sm font-medium text-secondary-500 mb-1">密码</label>
                    <input v-model="password" type="password" required
                        class="w-full px-3 py-2 border border-secondary-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500">
                </div>

                <div v-if="error" class="text-error-500 text-sm">
                    {{ error }}
                </div>

                <button type="submit"
                    class="w-full bg-primary-600 text-white py-2 px-4 rounded-md hover:bg-primary-700 transition duration-300">
                    {{ isLoginMode ? '登录' : '注册' }}
                </button>
            </form>

            <div class="mt-4 text-center">
                <button @click="isLoginMode = !isLoginMode" class="text-primary-600 hover:text-primary-700">
                    {{ isLoginMode ? '没有账户？去注册' : '已有账户？去登录' }}
                </button>
            </div>
        </section>

        <section v-else class="w-full max-w-md bg-white rounded-lg shadow-md p-6">
            <div class="text-center mb-6">
                <h2 class="text-2xl font-bold">用户信息</h2>
            </div>

            <div>
                <div v-for="(info, index) in userInfo" :key="index"
                    class="flex items-center justify-between p-4 bg-secondary-50">
                    <span class="text-secondary-500">{{ info.label }}</span>
                    <span class="font-medium text-primary-700" :class="{
                        'text-warning-700': info.isBalance,
                        'capitalize': info.isRole
                    }">
                        {{ info.value }}
                    </span>
                </div>
            </div>

            <div class="mt-6">
                <button @click="handleLogout"
                    class="w-full bg-danger-500 text-white py-2 px-4 rounded-md hover:bg-danger-600 transition duration-300">
                    登出
                </button>
            </div>
        </section>
    </main>
</template>