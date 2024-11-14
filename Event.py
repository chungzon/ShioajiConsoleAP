class Event:
    """事件類，用於傳遞消息和數據"""
    def __init__(self, event_type, data=None):
        """
        初始化事件
        :param event_type: 事件類型 (如 'log_message', 'progress_update' 等)
        :param data: 事件攜帶的數據
        """
        self.type = event_type
        self.data = data

class EventBus:
    """事件總線，用於處理事件的發布和訂閱"""
    def __init__(self):
        # 存儲所有訂閱者，格式為 {event_type: [handlers]}
        self._subscribers = {}

    def subscribe(self, event_type, handler):
        """
        訂閱特定類型的事件
        :param event_type: 事件類型
        :param handler: 處理事件的回調函數
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        if handler not in self._subscribers[event_type]:
            self._subscribers[event_type].append(handler)

    def unsubscribe(self, event_type, handler):
        """
        取消訂閱特定類型的事件
        :param event_type: 事件類型
        :param handler: 要移除的處理函數
        """
        if event_type in self._subscribers and handler in self._subscribers[event_type]:
            self._subscribers[event_type].remove(handler)

    def publish(self, event):
        """
        發布事件
        :param event: Event 實例
        """
        if event.type in self._subscribers:
            for handler in self._subscribers[event.type]:
                try:
                    handler(event)
                except Exception as e:
                    print(f"處理事件時發生錯誤: {e}")

    def clear(self):
        """清除所有訂閱"""
        self._subscribers.clear() 