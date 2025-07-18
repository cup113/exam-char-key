import { defineStore } from "pinia";
import { useLocalStorage } from "@vueuse/core";
import type { AiUsageResult } from "./types";

export const useSettingsStore = defineStore("settings", () => {
    const usageInfo = useLocalStorage("EC_usageInfo", {
        prompt_tokens: 0,
        prompt_price: 0,
        completion_tokens: 0,
        completion_price: 0,
    }); // 1 price = 1e-7 RMB

    function updateUsage(usageResult: AiUsageResult) {
        usageInfo.value.prompt_tokens += usageResult.prompt_tokens;
        usageInfo.value.completion_tokens += usageResult.completion_tokens;
        usageInfo.value.prompt_price += usageResult.input_unit_price * usageResult.prompt_tokens;
        usageInfo.value.completion_price += usageResult.output_unit_price * usageResult.completion_tokens;
    }

    return {
        usageInfo,
        updateUsage,
    };
});
