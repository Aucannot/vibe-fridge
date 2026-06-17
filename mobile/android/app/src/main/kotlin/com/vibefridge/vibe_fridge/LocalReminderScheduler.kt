package com.vibefridge.vibe_fridge

import android.app.AlarmManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import kotlin.math.max
import org.json.JSONArray
import org.json.JSONObject

object LocalReminderScheduler {
    fun scheduleFromChannel(context: Context, arguments: Any?) {
        val rows = parseChannelRows(arguments)
        cancelScheduledReminders(context, clearStoredRows = false)
        scheduleRows(context, rows)
        saveRows(context, rows)
    }

    fun restoreScheduledReminders(context: Context) {
        scheduleRows(context, loadRows(context))
    }

    fun cancelScheduledReminders(context: Context) {
        cancelScheduledReminders(context, clearStoredRows = true)
    }

    private fun scheduleRows(context: Context, rows: List<ReminderRow>) {
        val alarmManager = context.getSystemService(
            Context.ALARM_SERVICE,
        ) as AlarmManager
        rows.forEach { row ->
            val triggerAt = max(
                row.scheduledAtMillis,
                System.currentTimeMillis() + 30_000L,
            )
            val intent = Intent(context, ReminderNotificationReceiver::class.java)
                .putExtra(LocalNotificationContract.extraItemId, row.itemId)
                .putExtra(LocalNotificationContract.extraTitle, row.title)
                .putExtra(LocalNotificationContract.extraBody, row.body)
            val pendingIntent = PendingIntent.getBroadcast(
                context,
                LocalNotificationContract.requestCodeFor(row.itemId),
                intent,
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
            )
            alarmManager.set(AlarmManager.RTC_WAKEUP, triggerAt, pendingIntent)
        }
    }

    private fun cancelScheduledReminders(
        context: Context,
        clearStoredRows: Boolean,
    ) {
        val alarmManager = context.getSystemService(
            Context.ALARM_SERVICE,
        ) as AlarmManager
        val prefs = notificationPrefs(context)
        val itemIds = prefs.getStringSet(
            LocalNotificationContract.scheduledItemIdsKey,
            emptySet(),
        ) ?: emptySet()
        itemIds.forEach { itemId ->
            val intent = Intent(context, ReminderNotificationReceiver::class.java)
            val pendingIntent = PendingIntent.getBroadcast(
                context,
                LocalNotificationContract.requestCodeFor(itemId),
                intent,
                PendingIntent.FLAG_NO_CREATE or PendingIntent.FLAG_IMMUTABLE,
            )
            if (pendingIntent != null) {
                alarmManager.cancel(pendingIntent)
                pendingIntent.cancel()
            }
        }
        if (clearStoredRows) {
            prefs.edit()
                .remove(LocalNotificationContract.scheduledItemIdsKey)
                .remove(LocalNotificationContract.scheduledNotificationsKey)
                .apply()
        }
    }

    private fun saveRows(context: Context, rows: List<ReminderRow>) {
        val serialized = JSONArray().apply {
            rows.forEach { row ->
                put(
                    JSONObject()
                        .put("itemId", row.itemId)
                        .put("title", row.title)
                        .put("body", row.body)
                        .put("scheduledAtMillis", row.scheduledAtMillis),
                )
            }
        }.toString()
        notificationPrefs(context)
            .edit()
            .putStringSet(
                LocalNotificationContract.scheduledItemIdsKey,
                rows.map { row -> row.itemId }.toSet(),
            )
            .putString(
                LocalNotificationContract.scheduledNotificationsKey,
                serialized,
            )
            .apply()
    }

    private fun loadRows(context: Context): List<ReminderRow> {
        val raw = notificationPrefs(context).getString(
            LocalNotificationContract.scheduledNotificationsKey,
            null,
        ) ?: return emptyList()
        return try {
            val rows = mutableListOf<ReminderRow>()
            val array = JSONArray(raw)
            for (index in 0 until array.length()) {
                val item = array.optJSONObject(index) ?: continue
                val itemId = item.optString("itemId")
                val scheduledAtMillis = item.optLong("scheduledAtMillis")
                if (itemId.isBlank() || scheduledAtMillis <= 0L) {
                    continue
                }
                rows.add(
                    ReminderRow(
                        itemId = itemId,
                        title = item.optString("title", "库存提醒"),
                        body = item.optString(
                            "body",
                            "打开 vibe-fridge 查看详情",
                        ),
                        scheduledAtMillis = scheduledAtMillis,
                    ),
                )
            }
            rows
        } catch (ignored: Exception) {
            emptyList()
        }
    }

    private fun parseChannelRows(arguments: Any?): List<ReminderRow> {
        val rows = (arguments as? Map<*, *>)?.get("notifications") as? List<*>
            ?: emptyList<Any>()
        return rows.filterIsInstance<Map<*, *>>().mapNotNull { row ->
            val itemId = row["itemId"] as? String ?: return@mapNotNull null
            val scheduledAtMillis =
                (row["scheduledAtMillis"] as? Number)?.toLong()
                    ?: return@mapNotNull null
            ReminderRow(
                itemId = itemId,
                title = row["title"] as? String ?: "库存提醒",
                body = row["body"] as? String ?: "打开 vibe-fridge 查看详情",
                scheduledAtMillis = scheduledAtMillis,
            )
        }
    }

    private fun notificationPrefs(context: Context) = context.getSharedPreferences(
        LocalNotificationContract.prefsName,
        Context.MODE_PRIVATE,
    )
}

private data class ReminderRow(
    val itemId: String,
    val title: String,
    val body: String,
    val scheduledAtMillis: Long,
)
