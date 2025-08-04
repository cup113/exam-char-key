import { defineStore } from "pinia";
import { computed, nextTick, ref } from "vue";
import { useLocalStorage } from "@vueuse/core";
import { useApiStore } from "./api";
import { type AiUsageResult, User } from "./types";

interface BalanceDetail {
    id: string;
    created: string;
    delta: number;
    remaining: number;
    reason: string;
}

export const useUserStore = defineStore("settings", () => {
    const usageInfo = useLocalStorage("EC_usageInfo", {
        prompt_tokens: 0,
        prompt_price: 0,
        completion_tokens: 0,
        completion_price: 0,
    });


    const user = useLocalStorage("EC_user", User.empty(), {
        serializer: {
            read(raw) {
                return new User(JSON.parse(raw));
            },
            write(data) {
                return JSON.stringify(data);
            }
        }
    });
    const isGuest = computed(() => user.value.role.name === "Guest");
    const token = useLocalStorage("EC_token", "");
    const deepThinking = useLocalStorage('EC_deepThinking_v2', 1);


    // Balance Details
    const balanceDetails = ref<BalanceDetail[]>([]);
    const bdCurrentPage = ref(1);
    const bdTotalPages = ref(1);
    const bdLoading = ref(false);

    function updateUser(_user: User) {
        user.value = _user;
    }

    function updateToken(newToken: string) {
        token.value = newToken;
    }

    function updateUsage(usageResult: AiUsageResult) {
        usageInfo.value.prompt_tokens += usageResult.prompt_tokens;
        usageInfo.value.completion_tokens += usageResult.completion_tokens;
    }

    async function fetchBalanceDetails(page: number = 1) {
        bdLoading.value = true;
        try {
            const apiStore = useApiStore();
            const response = await apiStore.getBalanceDetails(page);
            balanceDetails.value = response.items;
            bdTotalPages.value = response.total_pages;
            bdCurrentPage.value = page;
        } catch (error) {
            console.error('Failed to fetch balance details:', error);
        } finally {
            bdLoading.value = false;
        }
    }

    async function login(email: string, password: string) {
        const apiStore = useApiStore();
        await apiStore.login(email, password, updateToken, updateUser);
        await fetchBalanceDetails();
    }

    async function register(email: string, password: string) {
        const apiStore = useApiStore();
        await apiStore.register(email, password, updateToken, updateUser);
        await fetchBalanceDetails();
    }

    async function getUserInfo() {
        const apiStore = useApiStore();
        apiStore.getUserInfo(updateUser, updateToken);
        fetchBalanceDetails();
    }

    async function logout() {
        token.value = "";
        getUserInfo();
    }

    nextTick(getUserInfo);

    return {
        user,
        isGuest,
        token,
        usageInfo,
        balanceDetails,
        bdCurrentPage,
        bdTotalPages,
        bdLoading,
        deepThinking,
        updateUsage,
        updateUser,
        getUserInfo,
        login,
        register,
        logout,
        fetchBalanceDetails,
    };
});