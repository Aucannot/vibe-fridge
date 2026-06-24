package com.vibefridge.vibe_fridge

import android.Manifest
import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build

class ReminderNotificationReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        val itemId = intent.getStringExtra(LocalNotificationContract.extraItemId)
            ?: return
        if (itemId.isBlank()) {
            return
        }
        val title = intent.getStringExtra(LocalNotificationContract.extraTitle)
            ?: "库存提醒"
        val body = intent.getStringExtra(LocalNotificationContract.extraBody)
            ?: "打开 vibe-fridge 查看详情"
        if (!hasNotificationPermission(context)) {
            return
        }
        val notificationManager = context.getSystemService(
            Context.NOTIFICATION_SERVICE
        ) as NotificationManager
        ensureChannel(notificationManager)

        val launchIntent = Intent(context, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_SINGLE_TOP
            putExtra(LocalNotificationContract.extraItemId, itemId)
        }
        val pendingIntent = PendingIntent.getActivity(
            context,
            LocalNotificationContract.requestCodeFor(itemId),
            launchIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )
        val builder = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            Notification.Builder(
                context,
                LocalNotificationContract.notificationChannelId,
            )
        } else {
            @Suppress("DEPRECATION")
            Notification.Builder(context)
        }
        val notification = builder
            .setSmallIcon(R.drawable.ic_notification)
            .setContentTitle(title)
            .setContentText(body)
            .setContentIntent(pendingIntent)
            .setAutoCancel(true)
            .build()
        try {
            notificationManager.notify(
                LocalNotificationContract.requestCodeFor(itemId),
                notification,
            )
        } catch (ignored: SecurityException) {
            return
        }
    }

    private fun hasNotificationPermission(context: Context): Boolean {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.TIRAMISU) {
            return true
        }
        return context.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) ==
            PackageManager.PERMISSION_GRANTED
    }

    private fun ensureChannel(notificationManager: NotificationManager) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) {
            return
        }
        val channel = NotificationChannel(
            LocalNotificationContract.notificationChannelId,
            LocalNotificationContract.notificationChannelName,
            NotificationManager.IMPORTANCE_DEFAULT,
        ).apply {
            description = LocalNotificationContract.notificationChannelDescription
        }
        notificationManager.createNotificationChannel(channel)
    }
}
