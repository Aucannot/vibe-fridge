package com.vibefridge.vibe_fridge

import android.Manifest
import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

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
                        LocalReminderScheduler.scheduleFromChannel(
                            this,
                            call.arguments,
                        )
                        result.success(null)
                    }
                    "cancelAll" -> {
                        LocalReminderScheduler.cancelScheduledReminders(this)
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

}
