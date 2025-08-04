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

// 修改 deepThinkingOptions，添加描述信息
const deepThinkingOptions = [
    { value: 0, label: '关闭', description: '关闭AI深度思考功能，仅提供快速回答', cost: '成本降低 98%' },
    { value: 1, label: '浅度模式', description: '启用浅度思考，提供基本的分析和解释', cost: '成本降低 70%' },
    { value: 2, label: '深度模式', description: '启用深度思考，提供详细的分析和推理过程', cost: '成本最高' },
];

const currentDeepThinkingOption = computed(() => {
    const option = deepThinkingOptions.find(opt => opt.value === userStore.deepThinking);
    return option || deepThinkingOptions[0];
});
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
                        class="w-full px-3 py-2 border border-secondary-500 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500">
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

            <div class="p-4">
                <div class="flex items-center justify-between">
                    <label class="text-secondary-700">
                        思考模式
                    </label>
                    <div class="text-sm text-secondary-500">
                        {{ currentDeepThinkingOption.label }}
                    </div>
                </div>
                <div class="flex gap-2 mt-2">
                    <button v-for="option in deepThinkingOptions" :key="option.value"
                        @click="userStore.deepThinking = option.value" :class="[
                            'flex-1 py-2 px-3 text-sm rounded-md transition-colors',
                            userStore.deepThinking === option.value
                                ? 'bg-primary-600'
                                : 'bg-secondary-100 text-secondary-700 hover:bg-secondary-200'
                        ]">
                        {{ option.label }}
                    </button>
                </div>
                <div class="mt-2 text-xs text-secondary-500">
                    {{ currentDeepThinkingOption.description }}（{{ currentDeepThinkingOption.cost }}）
                </div>
            </div>
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