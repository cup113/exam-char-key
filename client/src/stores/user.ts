import { defineStore } from "pinia";
import { nextTick } from "vue";
import { useLocalStorage } from "@vueuse/core";
import { useApiStore } from "./api";
import { type AiUsageResult, User } from "./types";

export const useUserStore = defineStore("settings", () => {
    const usageInfo = useLocalStorage("EC_usageInfo", {
        prompt_tokens: 0,
        prompt_price: 0,
        completion_tokens: 0,
        completion_price: 0,
    });

    const user = useLocalStorage("EC_user", new User({
        id: "",
        name: "",
        email: "",
        total_spent: 0,
        balance: 0,
        role: "guest",
    }), {
        serializer: {
            read(raw) {
                return new User(JSON.parse(raw));
            },
            write(data) {
                return JSON.stringify(data);
            }
        }
    });
    const token = useLocalStorage("EC_token", "");

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

    async function login(email: string, password: string) {
        const apiStore = useApiStore();
        await apiStore.login(email, password, updateToken, updateUser);
    }

    async function register(email: string, password: string) {
        const apiStore = useApiStore();
        await apiStore.register(email, password, updateToken, updateUser);
    }

    async function getUserInfo() {
        const apiStore = useApiStore();
        apiStore.getUserInfo(updateUser, updateToken);
    }

    async function logout() {
        token.value = "";
        user.value = new User({
            id: "",
            name: "",
            email: "",
            total_spent: 0,
            balance: 0,
            role: "guest",
        });
    }

    nextTick(getUserInfo)

    return {
        user,
        token,
        usageInfo,
        updateUsage,
        updateUser,
        getUserInfo,
        login,
        register,
        logout,
    };
});