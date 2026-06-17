package com.vibefridge.vibe_fridge

import android.Manifest
import android.app.AlarmManager
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel
import kotlin.math.max

class MainActivity : FlutterActivity() {
    private var notificationChannel: MethodChannel? = null
    private var permissionResult: MethodChannel.Result? = null
    private var launchItemId: String? = null

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        ensureNotificationChannel()
        launchItemId = intent?.getStringExtra(LocalNotificationContract.extraItemId)
        notificationChannel = MethodChannel(
            flutterEngine.dartExecutor.binaryMessenger,
            LocalNotificationContract.channelName,
        ).also { channel ->
            channel.setMethodCallHandler { call, result ->
                when (call.method) {
                    "initialize" -> result.success(permissionStatus())
                    "getPermissionStatus" -> result.success(permissionStatus())
                    "requestPermission" -> requestNotificationPermission(result)
                    "getLaunchItemId" -> {
                        val itemId = launchItemId
                        launchItemId = null
                        result.success(itemId)
                    }
                    "scheduleInventoryReminders" -> {
                        scheduleInventoryReminders(call.arguments)
                        result.success(null)
                    }
                    "cancelAll" -> {
                        cancelScheduledReminders()
                        result.success(null)
                    }
                    else -> result.notImplemented()
                }
            }
        }
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        val itemId = intent.getStringExtra(LocalNotificationContract.extraItemId)
        if (!itemId.isNullOrEmpty()) {
            launchItemId = itemId
            notificationChannel?.invokeMethod(
                "notificationTapped",
                mapOf("itemId" to itemId),
            )
        }
    }

    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray,
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode != LocalNotificationContract.permissionRequestCode) {
            return
        }
        permissionResult?.success(permissionStatus())
        permissionResult = null
    }

    private fun requestNotificationPermission(result: MethodChannel.Result) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.TIRAMISU ||
            checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) ==
            PackageManager.PERMISSION_GRANTED
        ) {
            result.success(permissionStatus())
            return
        }
        permissionResult = result
        requestPermissions(
            arrayOf(Manifest.permission.POST_NOTIFICATIONS),
            LocalNotificationContract.permissionRequestCode,
        )
    }

    private fun permissionStatus(): Map<String, Any> {
        val granted = Build.VERSION.SDK_INT < Build.VERSION_CODES.TIRAMISU ||
            checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) ==
            PackageManager.PERMISSION_GRANTED
        return mapOf(
            "supported" to true,
            "granted" to granted,
            "status" to if (granted) "granted" else "denied",
        )
    }

    private fun scheduleInventoryReminders(arguments: Any?) {
        val rows = (arguments as? Map<*, *>)?.get("notifications") as? List<*>
            ?: emptyList<Any>()
        cancelScheduledReminders()
        val scheduledItemIds = mutableSetOf<String>()
        val alarmManager = getSystemService(Context.ALARM_SERVICE) as AlarmManager
        rows.filterIsInstance<Map<*, *>>().forEach { row ->
            val itemId = row["itemId"] as? String ?: return@forEach
            val title = row["title"] as? String ?: "库存提醒"
            val body = row["body"] as? String ?: "打开 vibe-fridge 查看详情"
            val scheduledAtMillis =
                (row["scheduledAtMillis"] as? Number)?.toLong()
                    ?: return@forEach
            val triggerAt = max(
                scheduledAtMillis,
                System.currentTimeMillis() + 30_000L,
            )
            val intent = Intent(this, ReminderNotificationReceiver::class.java)
                .putExtra(LocalNotificationContract.extraItemId, itemId)
                .putExtra(LocalNotificationContract.extraTitle, title)
                .putExtra(LocalNotificationContract.extraBody, body)
            val pendingIntent = PendingIntent.getBroadcast(
                this,
                LocalNotificationContract.requestCodeFor(itemId),
                intent,
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
            )
            alarmManager.set(AlarmManager.RTC_WAKEUP, triggerAt, pendingIntent)
            scheduledItemIds.add(itemId)
        }
        notificationPrefs()
            .edit()
            .putStringSet(
                LocalNotificationContract.scheduledItemIdsKey,
                scheduledItemIds,
            )
            .apply()
    }

    private fun cancelScheduledReminders() {
        val alarmManager = getSystemService(Context.ALARM_SERVICE) as AlarmManager
        val itemIds = notificationPrefs().getStringSet(
            LocalNotificationContract.scheduledItemIdsKey,
            emptySet(),
        ) ?: emptySet()
        itemIds.forEach { itemId ->
            val intent = Intent(this, ReminderNotificationReceiver::class.java)
            val pendingIntent = PendingIntent.getBroadcast(
                this,
                LocalNotificationContract.requestCodeFor(itemId),
                intent,
                PendingIntent.FLAG_NO_CREATE or PendingIntent.FLAG_IMMUTABLE,
            )
            if (pendingIntent != null) {
                alarmManager.cancel(pendingIntent)
                pendingIntent.cancel()
            }
        }
        notificationPrefs()
            .edit()
            .remove(LocalNotificationContract.scheduledItemIdsKey)
            .apply()
    }

    private fun ensureNotificationChannel() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) {
            return
        }
        val notificationManager = getSystemService(
            Context.NOTIFICATION_SERVICE
        ) as NotificationManager
        val channel = NotificationChannel(
            LocalNotificationContract.notificationChannelId,
            LocalNotificationContract.notificationChannelName,
            NotificationManager.IMPORTANCE_DEFAULT,
        ).apply {
            description = LocalNotificationContract.notificationChannelDescription
        }
        notificationManager.createNotificationChannel(channel)
    }

    private fun notificationPrefs() = getSharedPreferences(
        LocalNotificationContract.prefsName,
        Context.MODE_PRIVATE,
    )
}
