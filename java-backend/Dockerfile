# Java 25の公式JDKイメージを使用
FROM eclipse-temurin:25-jdk-alpine

WORKDIR /app

# プロジェクトのファイルをすべてコンテナ内にコピー
COPY . .

# ▼【追加】gradlewにLinux用の実行権限を付与する
RUN chmod +x gradlew

# Gradleでビルドを実行
RUN ./gradlew bootJar --no-daemon

# アプリケーションが使用するポートを指定
EXPOSE 8080

# アプリケーションの起動コマンド
CMD ["java", "-jar", "build/libs/*.jar"]