import { defineStore } from "pinia";
import type { HistoryRecord } from "./types";
import { useLocalStorage } from "@vueuse/core";

export const useHistoryStore = defineStore("history", () => {
    const history = useLocalStorage<HistoryRecord[]>("EC_history", []);
    const MAX_HISTORY = 100;

    function exportHistory(selected: HistoryRecord[]) {
        const json = {
            version: 3,
            title: `文言文字词梳理 ${new Date().toLocaleString()}`,
            records: selected,
            footer: "",
            deckType: "type",
        };
        const blob = new Blob([JSON.stringify(json, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `history_${Date.now()}.json`;
        a.click();
        URL.revokeObjectURL(url);
    };

    function deleteHistory(selected: HistoryRecord[]) {
        history.value = history.value.filter(record => !selected.some(item => item.id === record.id));
    }

    function insertHistory(record: HistoryRecord) {
        history.value.unshift(record);
        if (history.value.length > MAX_HISTORY) {
            history.value.pop();
        }
    }

    return {
        history,
        exportHistory,
        deleteHistory,
        insertHistory,
    };
});
