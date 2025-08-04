import { defineStore } from "pinia";
import type { HistoryRecord } from "./types";
import { set, useLocalStorage } from "@vueuse/core";

export const useHistoryStore = defineStore("history", () => {
    const history = useLocalStorage<HistoryRecord[]>("EC_history", []);
    const MAX_HISTORY = 100;

    function exportHistory(selected: HistoryRecord[], format: 'json' | 'word' | 'apkg') {
        const json = {
            version: 3,
            title: `文言文字词梳理 ${new Date().toLocaleString()}`,
            records: selected,
            footer: "",
            deckType: "type",
        };

        if (format === 'json') {
            const blob = new Blob([JSON.stringify(json, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `history_${Date.now()}.json`;
            a.click();
            URL.revokeObjectURL(url);
        } else if (format === 'word' || format === 'apkg') {
            // 调用 API 生成 Word 或 APKG 文件
            fetch('https://anki.cup11.top/api/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(json),
            })
                .then(response => response.json())
                .then(data => {
                    const title = json.title.replace(/[\s\:\/\\]+/g, '_')
                    let url = "";
                    let filename = "";
                    if (format === 'word' && data.docx_filename) {
                        url = `https://anki.cup11.top/api/download/docx/${data.docx_filename}`;
                        filename = `${title}.docx`;
                    } else if (format === 'apkg' && data.apkg_filename) {
                        url = `https://anki.cup11.top/api/download/apkg/${data.apkg_filename}`;
                        filename = `${title}.apkg`;
                    }
                    fetch(url).then(response => response.blob()).then(blob => {
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = filename;
                        a.click();
                        setTimeout(() => URL.revokeObjectURL(url), 30 * 1000);
                    }).catch(e => {
                        console.error('下载失败:', e);
                        alert('导出失败，请稍后重试');
                    })
                })
                .catch(error => {
                    console.error('导出失败:', error);
                    alert('导出失败，请稍后重试');
                });
        }
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
