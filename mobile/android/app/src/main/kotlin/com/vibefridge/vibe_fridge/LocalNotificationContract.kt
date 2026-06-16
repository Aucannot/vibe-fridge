package com.vibefridge.vibe_fridge

object LocalNotificationContract {
    const val channelName = "vibe_fridge/local_notifications"
    const val notificationChannelId = "expiry_reminders"
    const val notificationChannelName = "过期提醒"
    const val permissionRequestCode = 4817
    const val prefsName = "vibe_fridge_notifications"
    const val scheduledItemIdsKey = "scheduled_item_ids"
    const val extraItemId = "item_id"
    const val extraTitle = "title"
    const val extraBody = "body"

    fun requestCodeFor(itemId: String): Int {
        return itemId.hashCode() and 0x7fffffff
    }
}
