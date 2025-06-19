import { defineStore } from 'pinia';

export const useCommonStore = defineStore('common', {
  state: () => ({
    logCache: [] as string[],
    startTime: '',
    eventSource: null as EventSource | null
  }),
  
  getters: {
    getLogCache: (state) => () => state.logCache,
    getStartTime: (state) => () => state.startTime
  },
  
  actions: {
    createEventSource() {
      if (this.eventSource) {
        this.eventSource.close();
      }
      
      this.eventSource = new EventSource('/api/log');
      this.eventSource.onmessage = (event) => {
        this.logCache.push(event.data);
        // 保持日志缓存在合理大小
        if (this.logCache.length > 1000) {
          this.logCache = this.logCache.slice(-500);
        }
      };
      
      this.eventSource.onerror = (error) => {
        console.error('EventSource failed:', error);
        this.eventSource?.close();
      };
    },
    
    closeEventSource() {
      if (this.eventSource) {
        this.eventSource.close();
        this.eventSource = null;
      }
    },
    
    updateStartTime() {
      this.startTime = new Date().toISOString();
    }
  }
});
