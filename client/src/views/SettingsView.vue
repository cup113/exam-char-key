<script lang="ts" setup>
import { useUserStore } from '@/stores/user';
import { computed, ref } from 'vue';
import { add_sep } from '@/stores/utils';
import BalanceDetails from '@/components/BalanceDetails.vue';
import { SwitchRoot, SwitchThumb } from 'reka-ui';

const userStore = useUserStore();

const email = ref('');
const password = ref('');
const isLoginMode = ref(true);
const error = ref('');

const userInfo = computed(() => [
    { label: '用户名', value: userStore.user.name },
    { label: '用户ID', value: userStore.user.id },
    { label: '邮箱', value: userStore.user.email },
    { label: '余额', value: add_sep(userStore.user.balance), isBalance: true },
    { label: '历史花费', value: add_sep(userStore.user.total_spent) },
    { label: '角色', value: userStore.user.role.name, isRole: true },
]);

const isGuest = computed(() => {
    return userStore.user.role.name === 'Guest';
})

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
    <main class="p-4 flex flex-col items-center gap-4">
        <section v-if="isGuest" class="ec-standard-card">
            <div class="justify-center">{{ isLoginMode ? '用户登录' : '用户注册' }}
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

            <div class="text-center">
                <button @click="isLoginMode = !isLoginMode" class="text-primary-600 hover:text-primary-700">
                    {{ isLoginMode ? '没有账户？去注册' : '已有账户？去登录' }}
                </button>
            </div>
        </section>

        <section class="ec-standard-card">
            <div class="justify-center">用户偏好</div>
            <label class="flex items-center gap-2 justify-center">
                深度思考模式
                <switch-root
                    class="w-8 h-5 shadow-sm flex data-[state=unchecked]:bg-secondary-300 data-[state=checked]:bg-primary-700 border border-secondary-300 data-[state=checked]:border-stone-700 rounded-full relative transition-[background]" v-model="userStore.deepThinking">
                    <switch-thumb
                        class="w-3.5 h-3.5 my-auto bg-secondary-50 text-xs flex items-center justify-center shadow-xl rounded-full transition-transform translate-x-0.5 will-change-transform data-[state=checked]:translate-x-full"></switch-thumb>
                </switch-root>
            </label>
        </section>

        <section class="ec-standard-card">
            <div class="justify-center">
                用户信息
            </div>

            <div>
                <div v-for="(info, index) in userInfo" :key="index"
                    class="flex items-center justify-between p-4 shadow-sm">
                    <span class="text-secondary-500 min-w-12">{{ info.label }}</span>
                    <span class="font-medium text-primary-700" :class="{
                        'text-warning-700': info.isBalance,
                        'capitalize': info.isRole
                    }">
                        {{ info.value }}
                    </span>
                </div>
            </div>

            <div>
                <div class="flex gap-2">
                    <button @click="userStore.getUserInfo()"
                        class="flex-1 bg-secondary-500 text-white py-2 px-4 rounded-md hover:bg-secondary-600 transition duration-300">
                        刷新
                    </button>
                    <button v-if="!isGuest" @click="handleLogout"
                        class="flex-1 bg-danger-500 text-white py-2 px-4 rounded-md hover:bg-danger-600 transition duration-300">
                        登出
                    </button>
                </div>
            </div>
        </section>

        <section>
            <balance-details></balance-details>
        </section>
    </main>
</template>